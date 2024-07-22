import asyncio
import os
import time
import json
from concurrent.futures import ThreadPoolExecutor

from botocore.exceptions import EndpointConnectionError
from fastapi import HTTPException
from mypy_boto3_sqs import SQSClient

# from app.user_account.user_account_actions import UserAccountActions
from app.actions.user_actions import UserActions
# from app.user_account.user_account_models import UserAccountCreate
from app.schemas.user_service_schemas import UserServiceCreate
from app.utilities.decorators import handle_reconnect
from app.worker.logging_format import init_logger
from app.worker.sqs_client import SQSClientSingleton
from app.worker.utils import WorkerUtils
from app.utilities.enums import SignonJobs

logger = init_logger("Account Worker")

RETRY_DELAY = .5  # Delay between retries in seconds
MAX_RETRIES = 4  # Maximum number of retries

ACCOUNT_QUEUE = os.environ.get("ACCOUNTS_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-accounts")


class AccountWorker:

    def __init__(self):
        self.default_queue = ACCOUNT_QUEUE
        self.queue_name = WorkerUtils.get_queue_name(self.default_queue)
        self.conn: SQSClient = SQSClientSingleton.get_instance(self.default_queue)
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=1)

    def reconnect(self):
        logger.magic_signon("Reconnecting to queue...")
        self.conn = SQSClientSingleton.reconnect(self.default_queue)

    @handle_reconnect
    def send_message(self, message: dict, queue_url: str):
        response = self.conn.send_message(
            QueueUrl=queue_url,
            DelaySeconds=1,
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
                    # runs in a separate thread to avoid blocking the event loop
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

            if "Messages" not in messages_received.keys():
                continue
            start_time = time.time()
            # logger.magic_signon(messages_received)
            # TODO: picking off the top message (only getting one anyway)
            msg_data = messages_received["Messages"][0]
            msg_body_dict: dict = json.loads(msg_data.get("Body") or "")
            receipt_handle = msg_data.get("ReceiptHandle")
            try:
                should_delete = await self.consume_job(msg_body_dict)

                if should_delete:
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
            return False, "Invalid SignonJobs Type"
        logger.magic_signon(f"Starting {event_type} job...")

        match SignonJobs(event_type):
            case SignonJobs.CREATE_USER:
                response = await self.create_user(msg_data)
            # case SignonJobs.CREATE_USER_ACCOUNT:
            #     response = await self.create_user_account(msg_data)
            # case SignonJobs.UPDATE_USER_ACCOUNT:
            #     response = await self.update_user_account(msg_data)
            case SignonJobs.MIGRATE_USER:
                response = await self.migrate_user(msg_data)
            case SignonJobs.SEND_AUTH_CODE:
                response = await self.send_auth_code(msg_data)
            case SignonJobs.ADD_NEW_SERVICE:
                response = await self.add_new_service(msg_data)
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

    async def create_user(self, msg_data: dict):
        new_user = await UserActions.handle_user_job(msg_data)

        if msg_data["source"] == "TREASURE_VAULT":
            if hasattr(new_user, "dict"):
                user_dict = new_user.dict()
            else:
                user_dict = new_user.to_dict()
            response = await self.send_response(msg_data, user_dict)
        elif msg_data["source"] == "PRODUCER":
            response = True
        else:
            response = False

        logger.magic_signon(f"User created for {new_user.first_name} {new_user.last_name}")
        return response

    # async def create_user_account(self, msg_data: dict):
    #     user_account_create = UserAccountCreate(**msg_data.get("body"))
    #     response = await UserAccountActions.create_account(user_account_create)
    #     response_dict = response.dict() if response else None
    #     if response_dict:
    #         logger.magic_signon(f"User Account Created for user with uuid: {response.user_account.user_uuid}")
    #     else:
    #         logger.magic_signon("User Account was not created.")
    #     return True

    async def migrate_user(self, msg_data: dict):
        body = msg_data.get("body")
        if body is None:
            raise ValueError("msg_data does not contain 'body'")
        if not isinstance(body, dict):
            raise ValueError("'body' is not a dictionary")

        user_uuid = body.get("user_uuid")
        if user_uuid is None:
            raise ValueError("'body' does not contain 'user_uuid'")
        user_service_create = UserServiceCreate(**body)
        migrate_user = await UserActions.confirm_code_migrate_user(user_uuid, user_service_create)
        response = await self.send_response(msg_data, migrate_user)
        if migrate_user:
            logger.magic_signon(f"Migration successful for user with uuid: {user_uuid}")
        else:
            logger.magic_signon("Migration was not successful")
        return response

    async def send_auth_code(self, msg_data: dict):
        body = msg_data.get("body")
        if body is None:
            raise ValueError("msg_data does not contain 'body'")
        if not isinstance(body, dict):
            raise ValueError("'body' is not a dictionary")

        auth_response = await UserActions.send_auth_code(body["user_uuid"], UserServiceCreate(**body), True)
        response = await self.send_response(msg_data, auth_response)
        if auth_response:
            logger.magic_signon("Auth code successfully sent.")
        else:
            logger.magic_signon("Auth code was not sent.")
        return response

    async def add_new_service(self, msg_data: dict):
        body = msg_data.get("body")
        if body is None:
            raise ValueError("msg_data does not contain 'body'")
        if not isinstance(body, dict):
            raise ValueError("'body' is not a dictionary")

        new_service = await UserActions.confirm_code_add_service(body["user_uuid"], UserServiceCreate(**body), True)
        service_dict = new_service.dict() if new_service else None
        response = await self.send_response(msg_data, service_dict)
        if new_service == "exists":
            logger.magic_signon("The provided service already exists")
        elif new_service:
            logger.magic_signon("New service successfully added.")
        else:
            logger.magic_signon("New service was not added.")
        return response

    # async def update_user_account(self, msg_data: dict):
    #     user_account_update = UserAccountCreate(**msg_data.get("body"))
    #     update_response = await UserAccountActions.handle_update_account_job(user_account_update)
    #     user_account_dict = update_response.dict() if update_response else None
    #     if user_account_dict:
    #         if hasattr(update_response, "user_uuid"):
    #             logger.magic_signon(f"User Account Updated for user with uuid: {update_response.user_uuid}")
    #         else:
    #             logger.magic_signon(f"User Account Updated for user with uuid: {update_response.user_account.user_uuid}")
    #     else:
    #         logger.magic_signon("User Account was not updated.")
    #     return True
