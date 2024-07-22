import os
import json
from time import time

from fastapi import HTTPException
from mypy_boto3_sqs import SQSClient

from app.utilities.decorators import handle_reconnect
from app.utilities.utils import GenerateUUID
from app.worker.logging_format import init_logger
from app.worker.sqs_client import SQSClientSingleton

logger = init_logger("Temp Worker")

SEGMENT_QUEUE = os.environ.get("SEGMENT_QUERY_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-query")
RESPONSE_QUEUE = os.environ.get("SEGMENT_RESPONSE_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-response")


class TempWorker:

    def __init__(self):
        self.conn: SQSClient = SQSClientSingleton.get_instance(SEGMENT_QUEUE)

    def reconnect(self):
        logger.magic_signon("[Temp Worker] Reconnecting to queue...")
        self.conn = SQSClientSingleton.reconnect(SEGMENT_QUEUE)

    @handle_reconnect
    def send_message(self, message: dict, queue_url: str):
        response = self.conn.send_message(
            QueueUrl=queue_url,
            DelaySeconds=1,
            MessageBody=json.dumps(message),
        )
        logger.magic_signon(response)

    def update_message_visibility(self, receipt_handle, queue):
        self.conn.change_message_visibility(
            QueueUrl=queue,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=0
        )

    @handle_reconnect
    async def temp_worker(self, job, queue, response_queue=None):
        msg_data = {}
        try:
            job_id = GenerateUUID.hex()
            job["job_id"] = job_id
            self.send_message(job, queue)

            start_time = time()

            if response_queue:
                while True:
                    if time() - start_time > 5:
                        raise Exception("Temp worker timed out waiting for response.")

                    msg_response = self.conn.receive_message(
                        QueueUrl=response_queue,
                        AttributeNames=["SentTimestamp"],
                        # TODO: only will get a single message right now
                        MaxNumberOfMessages=1,
                        MessageAttributeNames=["string",],
                        VisibilityTimeout=30,
                        WaitTimeSeconds=20
                    )
                    if not msg_response:
                        return None
                    msg_data = msg_response["Messages"][0]
                    msg_body_dict: dict = json.loads(msg_data.get("Body") or "")
                    receipt_handle = msg_data.get("ReceiptHandle")
                    if msg_body_dict["job_id"] == job_id:
                        self.conn.delete_message(
                            QueueUrl=SEGMENT_QUEUE,
                            ReceiptHandle=receipt_handle
                        )
                        return msg_body_dict
                    else:
                        self.update_message_visibility(msg_response.receipt_handle, response_queue)
        except HTTPException as e:
            event_type = msg_data.get("eventType")
            logger.magic_signon(f"[Temp Worker] HTTP error processing {event_type} job: {e.detail}")
        except Exception as e:
            event_type = msg_data.get("eventType")
            logger.magic_signon(f"[Temp Worker] {event_type} job error: {e.__class__.__name__}: {e}")
