import os
from threading import Lock

import boto3
from mypy_boto3_sqs import SQSClient

from app.worker.utils import WorkerUtils

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


class SQSClientSingleton:
    _instance = None
    _lock = Lock()

    @classmethod
    def get_instance(cls, queue_url):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    endpoint_url = WorkerUtils.get_base_uri(queue_url)
                    cls._instance: SQSClient = boto3.client("sqs", region_name=AWS_REGION, endpoint_url=endpoint_url)
        return cls._instance

    @classmethod
    def reconnect(cls, queue_url):
        with cls._lock:
            endpoint_url = WorkerUtils.get_base_uri(queue_url)
            cls._instance: SQSClient = boto3.client("sqs", region_name=AWS_REGION, endpoint_url=endpoint_url)
        return cls._instance
