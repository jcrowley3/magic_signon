import asyncio
import os
import time
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from botocore.exceptions import EndpointConnectionError
from fastapi import HTTPException
from mypy_boto3_sqs import SQSClient

from app.actions.user_actions import UserActions
from app.schemas.user_schemas import UserAlt
from app.utilities.decorators import handle_reconnect
from app.worker.logging_format import init_logger
from app.worker.sqs_client import SQSClientSingleton
from app.worker.utils import WorkerUtils
from app.models.user_models import UserModelDB
from app.utilities.enums import SignonJobs

logger = init_logger("Segment Worker")

RETRY_DELAY = .5  # Delay between retries in seconds
MAX_RETRIES = 3  # Maximum number of retries

ACCOUNT_QUEUE = os.environ.get("ACCOUNTS_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-accounts")
SEGMENT_QUEUE = os.environ.get("SEGMENT_QUERY_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-query")
RESPONSE_QUEUE = os.environ.get("SEGMENT_RESPONSE_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-response")


class SegmentWorker:

    def __init__(self):
        self.default_queue = SEGMENT_QUEUE
        self.queue_name = WorkerUtils.get_queue_name(self.default_queue)
        self.conn: SQSClient = SQSClientSingleton.get_instance(self.default_queue)
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=1)

    def reconnect(self):
        logger.magic_signon("Reconnecting to queue...")
        self.conn = SQSClientSingleton.reconnect(self.default_queue)

    @handle_reconnect
    def send_message(self, message: dict, queue_url: str):
        if queue_url is None:
            raise ValueError("Queue URL is None.")
        response = self.conn.send_message(
            QueueUrl=queue_url,
            DelaySeconds=0,
            MessageBody=json.dumps(message),
        )
        logger.magic_signon(response)

    def update_message_visibility(self, receipt_handle, queue):
        logger.treasure_vault("Unable to process job. Putting job back in queue.")
        self.conn.change_message_visibility(
            QueueUrl=queue,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=0
        )

    async def worker(self):
        logger.magic_signon(f"Watching \033[92m{self.queue_name}\033[0m queue...")
        while True:
            for _ in range(MAX_RETRIES):
                try:
                    messages_received = await self.loop.run_in_executor(
                        self.executor,
                        lambda: self.conn.receive_message(
                            QueueUrl=self.default_queue,
                            AttributeNames=["SentTimestamp"],
                            MaxNumberOfMessages=1,  # TODO: only will get a single message right now
                            MessageAttributeNames=["string",],
                            VisibilityTimeout=30,
                            WaitTimeSeconds=20
                        )
                    )
                    break

                except self.conn.exceptions.QueueDoesNotExist:
                    logger.magic_signon("Queue does not exist. Retrying...")
                    await asyncio.sleep(RETRY_DELAY)
                    logger.magic_signon("Retrying to receive messages...")
                    continue
                except EndpointConnectionError:
                    logger.magic_signon("Endpoint connection error.")
                    self.reconnect()
                    continue
                except asyncio.CancelledError:
                    logger.magic_signon("Worker cancelled.")
                    return
                except Exception as e:
                    error_name = e.__class__.__name__
                    logger.magic_signon(f"Error receiving messages: {error_name}-{e}")
                    raise e
            else:
                # If we've exhausted all retries and still failed, reconnect
                logger.magic_signon("Max retries reached. Attempting Reconnect...")
                self.reconnect()
                continue

            start_time = time.time()

            if "Messages" not in messages_received.keys():
                continue
            # logger.magic_signon(messages_received)
            # TODO: picking off the top message (only getting one anyway)
            msg_data = messages_received["Messages"][0]
            msg_body_dict: dict = json.loads(msg_data.get("Body") or "")
            receipt_handle = msg_data.get("ReceiptHandle")
            if receipt_handle is None:
                logger.magic_signon("Receipt handle is None. Skipping message processing.")
                raise Exception
            try:
                should_delete = await self.consume_job(msg_body_dict)

                if should_delete:
                    if receipt_handle is not None:
                        self.conn.delete_message(
                            QueueUrl=self.default_queue,
                            ReceiptHandle=receipt_handle
                        )
                else:
                    self.update_message_visibility(receipt_handle, self.default_queue)

            except HTTPException as e:
                event_type = msg_body_dict.get("eventType")
                job_error = f"HTTP error processing {event_type} job: {e.detail}"
                logger.magic_signon(f"[Worker] {job_error}")
                self.update_message_visibility(receipt_handle, self.default_queue)
            except Exception as e:
                event_type = msg_body_dict.get("eventType")
                job_error = f"Error processing job . {e.__class__.__name__}: {e}"
                logger.magic_signon(f"[Worker] Moving {event_type} job to main queue.")
                self.update_message_visibility(receipt_handle, self.default_queue)

            end_time = time.time()
            duration = end_time - start_time
            logger.magic_signon(f"{msg_body_dict['eventType']} job processed in {format(duration, '.5f')} seconds!")

    async def consume_job(self, msg_data: dict):
        response = False
        event_type = msg_data.get("eventType")
        try:
            event_type = SignonJobs(event_type)
        except ValueError:
            # No matching event type found
            logger.magic_signon(f"Invalid event type: {event_type}")
            return False
        logger.magic_signon(f"Starting {event_type} job...")

        match SignonJobs(event_type):
            case SignonJobs.MOCK_GET_SURVEY_RESPONSE:
                logger.magic_signon(f"Test: Survey response received for Survey {msg_data['body']['surveyId']}")
                response = True
            case SignonJobs.GET_USER:
                response = await self.get_user(msg_data)
            case SignonJobs.ALT_GET_USER:
                response = await self.alt_get_user(msg_data)
            # case SignonJobs.GET_USERS_FOR_REWARD_CREATION:
            #     response = await self.get_users_for_reward_creation(msg_data)
            case _:
                # No matching event type found
                response = False
        return response

    async def send_response(self, job_data: dict, response_body: dict, status: str = None):
        job = self.response_job(job_data, response_body, status)
        self.send_message(job, queue_url=job_data["response_tube"])
        return True

    def response_job(self, job_data: dict, response_body: dict, status: str = None):
        response_payload = WorkerUtils.build_job_payload(
            event_type=f"{job_data['eventType']}_RESPONSE",
            source="MAGIC_SIGNON",
            response_body=response_body,
            response_tube=job_data["response_tube"],
            job_id=job_data["job_id"],
            response_status=status or "success"
        )
        return response_payload

    async def get_user(self, msg_data: dict):
        body = msg_data.get("body")
        if body is None:
            raise ValueError("msg_data does not contain 'body'")
        if not isinstance(body, dict):
            raise ValueError("'body' is not a dictionary")

        user_uuid = body.get("user_uuid")
        if user_uuid is None:
            raise ValueError("'body' does not contain 'user_uuid'")

        user: UserModelDB = await UserActions.get_user(user_uuid)
        user_dict = user.to_dict() if user else None
        response = await self.send_response(msg_data, user_dict)
        if user_dict:
            logger.magic_signon(f"User created for {user.first_name} {user.last_name}")
        else:
            logger.magic_signon(f"No user found for: {user_uuid}")
        return response

    async def alt_get_user(self, msg_data: dict):
        user_data = UserAlt(**msg_data.get("body"))
        user: UserModelDB = await UserActions.get_user_by_service_id(user_data.service_user_id)
        user_dict = user.to_dict() if user else None
        response = await self.send_response(msg_data, user_dict)
        if user_dict:
            logger.magic_signon(f"Got user: {user.first_name} {user.last_name}")
        else:
            logger.magic_signon(f"No user found for: {user_data.service_user_id}")
        return response

    @classmethod
    async def user_matches_segments(cls, user: dict, segments: list):
        for segment in segments:
            segment_values = await cls.convert_list_strings_to_lowercase(segment["values"])
            user_value = user["segment_metadata"].get(segment["field"], "").lower()
            if segment["operator"] == "=":
                if user_value not in segment_values:
                    return False
            elif segment["operator"] == "!=":
                if user_value in segment_values:
                    return False
        return True

    async def send_message_batch(self, batch, response_tube_url):
        entries = [{
            'Id': str(index),  
            'MessageBody': json.dumps(message) 
        } for index, message in enumerate(batch)]

        try:
            response = self.conn.send_message_batch(
                QueueUrl=response_tube_url,
                Entries=entries
            )

            if response.get('Failed'):
                print("Some messages failed to send:", response['Failed'])
            else:
                print("Batch sent successfully.")
        except Exception as e:
            print(f"Failed to send batch: {e}")

    async def send_messages_in_batches(self, messages, response_tube, batch_size=10):
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            await self.send_message_batch(batch, response_tube)

    @staticmethod
    async def get_hired_on_cap(onboarding_period: int):
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        start_of_day_epoch = int(start_of_day.timestamp())
        onboarding_period_epoch = onboarding_period*24*60*60
        return start_of_day_epoch - onboarding_period_epoch

    @staticmethod
    async def convert_list_strings_to_lowercase(input_item):
        if isinstance(input_item, list) and all(isinstance(element, str) for element in input_item):
            return [element.lower() for element in input_item]
        else:
            return input_item

    # TODO: magic_login, refactor or remove
    # async def get_users_for_reward_creation(self, msg_data: dict):
    #     body = msg_data.get("body", {})
    #     company_id = body.get("company_id")
    #     if not company_id:
    #         logger.magic_signon("No company_id provided in job data")
    #         return False
    #     # TODO: magic_login, refactor or remove
    #     if body.get("rule_type", "") == "ONBOARDING":
    #         hired_on_cap = await self.get_hired_on_cap(body["onboarding_period"])
    #         users = await UserActions.get_user_data_by_company_id(company_id, hired_on_cap)
    #     else:
    #         users = await UserActions.get_user_data_by_company_id(company_id)
    #     if not users:
    #         logger.magic_signon(f"No users found for company_id: {company_id}")
    #         return True

        # dict_users_list = [user._asdict() for user in users]
        # users_to_send = []
        # segmented_by = body.get("segmented_by")
        # if segmented_by:
        #     users_to_send = [user for user in dict_users_list if await self.user_matches_segments(user, segmented_by)]
        # else:
        #     users_to_send = dict_users_list

        # users_batches = [users_to_send[i:i+10] for i in range(0, len(users_to_send), 10)]
        # messages_to_send = []
        # for batch in users_batches:
        #     payload = {
        #         "rule_data": body,
        #         "users": batch 
        #     }
        #     message = WorkerUtils.build_job_payload(
        #         "CREATE_REWARD_FOR_USERS",  
        #         "MAGIC_SIGNON",
        #         payload
        #     )
        #     messages_to_send.append(message)
        # await self.send_messages_in_batches(messages_to_send, msg_data.get("response_tube"))

        # logger.magic_signon(f"Users found for company_id: {company_id}")
        # return users
