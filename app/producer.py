#!/usr/bin/env python3

import os
import signal
import statistics
import sys
import time
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3
import numpy as np
from faker import Faker
from mypy_boto3_sqs import SQSClient

from app.utilities.utils import GenerateUUID
from app.worker.logging_format import init_logger
from app.worker.utils import WorkerUtils

logger = init_logger("Test Producer")
faker = Faker()

ENV = os.environ.get("ENV", "local")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "foo")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "bar")
# TODO: Remove
# MAGIC_SIGNON_ACCOUNT_QUEUE = os.environ.get("ACCOUNTS_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-accounts")
MAGIC_SIGNON_SEGMENT_QUEUE = os.environ.get("SEGMENT_QUERY_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-query")
TREASURE_VAULT_RESPONSE_QUEUE = os.environ.get("SEGMENT_RESPONSE_QUEUE_URL", "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-response")

metadata = {
    "department": "engineering",
    "city": "portland",
    "country": "united states of america",
    "region": "north america"
}


def handle_reconnect(func):
    def wrapper(self, *args, **kwargs):
        retries = 3
        for _ in range(retries):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}: {e}")
                self.reconnect()
        print(f"Failed to execute {func.__name__} after {retries} retries.")
    return wrapper


class JobProducer:
    def __init__(self):
        self.conn: SQSClient = self.connect_to_sqs()
        self.stopped = False

    def connect_to_sqs(self) -> Any:
        # FYI: the producer requires the endpoint_url to be formated as such:
        # "http://sqs.us-east-1.localhost.localstack.cloud:4566"
        localstack_endpoint = WorkerUtils.get_base_uri(MAGIC_SIGNON_SEGMENT_QUEUE, "producer")
        if ENV.lower() in ["local"]:
            client: SQSClient = boto3.client("sqs", region_name=AWS_REGION, endpoint_url=localstack_endpoint, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        else:
            client: SQSClient = boto3.client("sqs", region_name=AWS_REGION, endpoint_url=localstack_endpoint)

        return client

    def reconnect(self):
        print("Reconnecting to queue...")
        self.conn.close()
        self.conn = self.connect_to_sqs()

    @handle_reconnect
    def put_job(self, job, queue):
        self.conn.send_message(
            QueueUrl=queue,
            MessageBody=json.dumps(job),
            DelaySeconds=0
        )

    def produce_jobs(self):
        jobs = [
            self.reward_job(),
            self.survey_job()
        ]
        for _ in range(10):
            for job in jobs:
                self.put_job(job, TREASURE_VAULT_RESPONSE_QUEUE)

    def fake_bday(self):
        return int(faker.date_time_between(start_date="-50y", end_date="-18y").timestamp())

    def stop_interactive_input(self, signal, frame):
        print("\nStopping it...")
        self.stopped = True
        raise KeyboardInterrupt

    def stop_loop_jobs(self, signal, frame):
        print("Stopping Looped Job Producer...")
        self.stopped = True

    @handle_reconnect
    def add_job_interactively(self, job_type=None):
        job = None
        queue = None
        selection = ""
        try:
            while True:
                if not job_type:
                    selection = input(
                        "Select the type of job to add to the queue:\n"
                        "  1: TEST TREASURE_VAULT RESPONSE QUEUE\n"
                        "  2: Test Misnamed Job -> Dead Letter Queue\n"
                        "  3: Start Looped Job Producer\n"
                        "  4: Add 1k jobs\n"
                        "MAGIC_SIGNON Jobs:\n"
                        "  5: wrong_job_test -> Dead Letter Queue\n"
                        "  6: MOCK_GET_SURVEY_RESPONSE (segment)\n"
                        # TODO: Remove
                        # "  7: CREATE_USER (account)\n"
                        # "  8: CREATE_USER_ACCOUNT (account)\n"
                        # "  9: CREATE HARD CODED USER ACCOUNT (account)\n"
                        # "  10: UPDATE HARD CODED USER ACCOUNT (account)\n"
                        "  11: CREATE REWARDS BY COMPANY ID (segment)\n"
                        "  12: CREATE REWARDS BY SEGMENTATION (segment)\n"
                        # cases that are not in use at the moment
                        # "  9: SEND_AUTH_CODE, migrate\n"
                        # "  10: SEND_AUTH_CODE, add_service\n"
                        # "  11: MIGRATE_USER + auth code\n"
                        # "  12: ADD_NEW_SERVICE + auth code\n"
                        # "  13: DRAIN THE MAGIC_SIGNON QUEUE\n"
                        # "  14: DRAIN THE TREASURE_VAULT QUEUE\n"
                        "  0: Exit\n"
                        "----------------\n"
                        "Your choice: "
                    )

                parts = selection.split()
                job_type = str(parts[0])
                # if len(parts) > 1:
                #     auth_code = int(parts[1])

                match job_type:
                    case "1":
                        queue = TREASURE_VAULT_RESPONSE_QUEUE
                        job = self.treasure_vault_test_job()
                    case "2":
                        queue = TREASURE_VAULT_RESPONSE_QUEUE
                        job = self.wrong_job_test()
                    case "3":
                        signal.signal(signal.SIGINT, self.stop_loop_jobs)
                        self.loop_jobs()
                        signal.signal(signal.SIGINT, self.stop_interactive_input)
                    case "4":
                        self.bulk_add_jobs(50)
                    case "5":
                        queue = MAGIC_SIGNON_SEGMENT_QUEUE
                        job = self.wrong_job_test()
                    case "6":
                        queue = MAGIC_SIGNON_SEGMENT_QUEUE
                        job = self.survey_job()
                    # TODO: Remove
                    # case "7":
                    #     queue = MAGIC_SIGNON_ACCOUNT_QUEUE
                    #     job = self.user_job()
                    # case "8":
                    #     queue = MAGIC_SIGNON_ACCOUNT_QUEUE
                    #     job = self.user_account_job()
                    # case "9":
                    #     queue = MAGIC_SIGNON_ACCOUNT_QUEUE
                    #     job = self.user_account_job(True)
                    # case "10":
                    #     queue = MAGIC_SIGNON_ACCOUNT_QUEUE
                    #     job = self.update_user_account_job()
                    case "11":
                        queue = MAGIC_SIGNON_SEGMENT_QUEUE
                        job = self.create_rewards_by_company_id()
                    case "12":
                        queue = MAGIC_SIGNON_SEGMENT_QUEUE
                        job = self.create_rewards_by_company_id(True)
                    # cases that are not in use at the moment
                    # case "9":
                    #     queue = ya_queue
                    #     job = self.send_auth_code_migrate_job()
                    # case "10":
                    #     queue = ya_queue
                    #     job = self.send_auth_code_add_service_job()
                    # case "11":
                    #     queue = ya_queue
                    #     job = self.migrate_user_job(auth_code)
                    # case "12":
                    #     queue = ya_queue
                    #     job = self.add_new_service(auth_code)
                    # case "13":
                    #     queue = ya_queue
                    #     job = self.drain_the_queue(queue)
                    # case "14":
                    #     queue = ms_queue
                    #     job = self.drain_the_queue(queue)
                    case "0" | "exit":
                        break
                    case _:
                        print("Invalid selection.")

                if job:
                    # status = self.conn.stats_queue(queue)["current-jobs-ready"]
                    self.put_job(job, queue)
                    # print(f"{queue} Jobs: {status}\n")
                    job = None
                job_type = None
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting...")
            sys.exit(0)

    # TODO: Remove
    # def client_user_job(self):
    #     first_name = faker.first_name()
    #     last_name = faker.last_name()
    #     email = f"{first_name.lower()}.{last_name.lower()}@testmail.com"

    #     return WorkerUtils.build_job_payload(
    #         "CREATE_CLIENT_USER",
    #         "PRODUCER",
    #         {
    #             "client_uuid": "ca723b34b08e4e319c8d2e6770815679c69aaf4a8e574f518b1e34",
    #             "user_uuid": "9ae67bd3bac022ceb63c364973f7b1c3bd6a14eedae0ab9f62a28790",
    #             "user": {"first_name": first_name, "last_name": last_name, "work_email": email}
    #         }
    #     )

    def treasure_vault_test_job(self):
        return WorkerUtils.build_job_payload(
            "TEST TREASURE_VAULT RESPONSE QUEUE",
            "PRODUCER",
            {"queue_test": "Testing the treasure_vault response queue."}
        )

    def reward_job(self):
        return WorkerUtils.build_job_payload(
            "MOCK_REWARD_SCHEDULED",
            "PRODUCER",
            {
                "surveyId": "aebQTOSw",
                "experience": {"concierge": "Jennifer", "name": "Skydiving"},
                "recipient": {"name": "Jane Doe", "email": "jane@doe.com"}
            }
        )

    def wrong_job_test(self):
        """This sends a job with an incorrect job name to test handling of incorrect jobs."""
        return WorkerUtils.build_job_payload(
            "WRONG_EVENT_TYPE",
            "PRODUCER",
            {"dogs_name": "Spot"}
        )

    def survey_job(self):
        return WorkerUtils.build_job_payload(
            "MOCK_GET_SURVEY_RESPONSE",
            "PRODUCER",
            {"surveyId": "aebQTOSw"}
        )

    def user_job(self):
        first_name = faker.first_name()
        last_name = faker.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@testmail.com"
        phone_number = f"+{faker.random_number(digits=10)}"
        company_id = faker.random_number(digits=1)

        return WorkerUtils.build_job_payload(
            "CREATE_USER",
            "PRODUCER",
            {
                "user": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone_number": phone_number,
                    "company_id": company_id,
                }
            }
        )

    @staticmethod
    def generate_random_hired_on_utc():
        now_utc = datetime.utcnow()
        start_date = now_utc - timedelta(days=30)
        end_date = now_utc - timedelta(days=1)
        random_date = start_date + (end_date - start_date) * random.random()
        return random_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # TODO: Remove
    def user_account_job(self, hard_coded_user=False):
        if hard_coded_user:
            return WorkerUtils.build_job_payload(
                "CREATE_USER_ACCOUNT",
                "PRODUCER",
                {
                    "first_name": "Tiger",
                    "last_name": "Woods",
                    "email_address": "tiger.woods@fakesandbox.mail",
                    "latitude": None,
                    "longitude": None,
                    "time_birthday": "1988-12-22T05:51:59.444336-08:00",
                    "hired_on": self.generate_random_hired_on_utc(),
                    "account_id": 1234,
                    "account_gid": "fbb9f443-cf24-42b1-bf3d-ac14172de5ae",
                    "company_id": "18",
                    "company_gid": "6cdcf917-a0da-4445-93ec-d51d662c60c6",
                    "deactivated_at": None,
                    "employee_id": 12345,
                    "manager_id": [68],
                    "segment_metadata": metadata
                }
            )

        first_name = faker.first_name()
        last_name = faker.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@testmail.com"
        account_id = faker.random_number(digits=5)
        employee_id = faker.random_number(digits=5)
        manager_id_1 = faker.random_number(digits=5)
        manager_id_2 = faker.random_number(digits=5)

        return WorkerUtils.build_job_payload(
            "CREATE_USER_ACCOUNT",
            "PRODUCER",
            {
                "first_name": first_name,
                "last_name": last_name,
                "email_address": email,
                "latitude": None,
                "longitude": None,
                "time_birthday": "1988-12-22T05:51:59.444336-08:00",
                "hired_on": self.generate_random_hired_on_utc(),
                "account_id": account_id,
                "account_gid": str(GenerateUUID.default()),
                "company_id": "18",
                "company_gid": "6cdcf917-a0da-4445-93ec-d51d662c60c6",
                "deactivated_at": None,
                "employee_id": employee_id,
                "manager_id": [manager_id_1, manager_id_2],
                "segment_metadata": {
                    "department": faker.job(),
                    "city": faker.city(),
                    "country": faker.country(),
                    "state": faker.state()
                }
            }
        )

    # TODO: Remove
    def update_user_account_job(self):
        return WorkerUtils.build_job_payload(
            "UPDATE_USER_ACCOUNT",
            "PRODUCER",
            {
                "first_name": "Tigerino",
                "last_name": "Wooderick",
                "email_address": "tiger.woods@fakesandbox.mail",
                "latitude": None,
                "longitude": None,
                "time_birthday": "1988-12-22T05:51:59.444336-08:00",
                "hired_on": "2022-12-22T05:51:59.444336-08:00",
                "account_id": 1234,
                "account_gid": "fbb9f443-cf24-42b1-bf3d-ac14172de5ae",
                "company_id": "18",
                "company_gid": "6cdcf917-a0da-4445-93ec-d51d662c60c6",
                "deactivated_at": int(datetime.now(timezone.utc).timestamp()),
                "employee_id": 12345,
                "manager_id": [98765],
                "segment_metadata": metadata
            }
        )

    def send_auth_code_migrate_job(self):
        return WorkerUtils.build_job_payload(
            "SEND_AUTH_CODE",
            "PRODUCER",
            {
                "user_uuid": "0fd169086d1a396ebcf45db9ac43eee34ea4fd1ca37b9c6bde6f0c1b",
                "service_type": "email",
                "service_user_id": "jcrowley317@gmail.com"
            }
        )

    def send_auth_code_add_service_job(self):
        return WorkerUtils.build_job_payload(
            "SEND_AUTH_CODE",
            "PRODUCER",
            {
                "user_uuid": "06ad1e1f05a61ab1ac423d5a6fb969193305145100c888a069eaacbf",
                "service_type": "email",
                "service_user_id": "jcrowley317@gmail.com"
            }
        )

    def migrate_user_job(self, auth_code):
        return WorkerUtils.build_job_payload(
            "MIGRATE_USER",
            "PRODUCER",
            {
                "user_uuid": "06ad1e1f05a61ab1ac423d5a6fb969193305145100c888a069eaacbf",
                "service_type": "email",
                "service_user_id": "jcrowley317@gmail.com",
                "auth_code": auth_code,
                "is_personal": False
            }
        )

    def add_new_service(self, auth_code):
        return WorkerUtils.build_job_payload(
            "ADD_NEW_SERVICE",
            "PRODUCER",
            {
                "user_uuid": "06ad1e1f05a61ab1ac423d5a6fb969193305145100c888a069eaacbf",
                "service_type": "email",
                "service_user_id": "jcrowley317@gmail.com",
                "auth_code": auth_code,
                "is_personal": True
            }
        )

    def create_rewards_by_company_id(self, segmented: bool = False):
        # create a single user, for the case where there might not be any users yet
        # queue = MAGIC_SIGNON_ACCOUNT_QUEUE
        # job = self.user_job()
        # self.put_job(job, queue)
        # time.sleep(.5)

        body = {
            "company_id": 18
        }
        if segmented:
            body = {
                "queryable_fields": {
                    "manager_id": 68,
                    "company_id": 18
                },
                "segmented_by": {
                    "city": "bend",
                    "state": "oregon"
                }
            }

        return WorkerUtils.build_job_payload(
            "GET_USERS_FOR_REWARD_CREATION",
            "TREASURE_VAULT",
            body,
            TREASURE_VAULT_RESPONSE_QUEUE
        )

    def bulk_add_jobs(self, batches):
        logger.producer(f"[Producer] {batches*20} new jobs...")
        for i in range(1, batches + 1):
            self.produce_jobs()
            if i % 10 == 0:
                print(f"Jobs produced: {i*20}")
        print("-" * 20)

    @handle_reconnect
    def loop_jobs(self):
        logger.producer("[Producer] Starting Looped Job Producer...")
        last_job_count = None
        times = []
        batch_averages = []
        beginning_start_time = time.time()
        start_time = time.time()

        while not self.stopped:
            response = self.conn.get_queue_attributes(
                QueueUrl=MAGIC_SIGNON_SEGMENT_QUEUE,
                AttributeNames=["ApproximateNumberOfMessages"]
            )
            job_total = int(response["Attributes"]["ApproximateNumberOfMessages"])

            if job_total != last_job_count or job_total == 0:
                if job_total <= 20:
                    end_time = time.time()
                    times.append(end_time - start_time)
                    avg_time = sum(times) / len(times)
                    batch_averages.append(avg_time)
                    logger.producer(f"[Producer] Average time for this batch of jobs: {avg_time:.5f} sec")
                    start_time = time.time()  # reset start_time
                    times = []  # reset times
                    self.produce_jobs()
                else:
                    pass
                last_job_count = job_total

        if batch_averages:
            batch_averages.remove(min(batch_averages))
        if batch_averages:
            total_avg = sum(batch_averages) / len(batch_averages)
            rolling_avg = sum(batch_averages[-5:]) / min(5, len(batch_averages))
            total_time = time.time() - beginning_start_time
            min_time = min(batch_averages)
            max_time = max(batch_averages)
            if len(batch_averages) >= 2:
                std_dev = statistics.stdev(batch_averages)
            else:
                std_dev = 0
            percentile_95 = np.percentile(batch_averages, 95)
            print("\nResults:")
            print(f"Total average time: {total_avg:.5f} sec")
            print(f"Rolling average time for the last 5 batches: {rolling_avg:.5f} sec")
            print(f"Min time: {min_time:.5f} sec")
            print(f"Max time: {max_time:.5f} sec")
            print(f"Standard deviation: {std_dev:.5f} sec")
            print(f"95th percentile time: {percentile_95:.5f} sec")
            print(f"Total batches: {len(batch_averages)}")
            print(f"Total jobs created: {len(batch_averages) * 20}")
            print(f"Total elapsed time: {total_time:.5f} sec")
            print("-" * 20)

    def drain_the_queue(self, queue):
        pass
        return True

        # self.conn.watch(queue)

        # # Drain the queue
        # while True:
        #     try:
        #         job = self.conn.reserve(timeout=0)
        #         self.conn.delete(job)
        #     except greenstalk.TimedOutError:
        #         # Break the loop if no job is found within the timeout
        #         break

        # print(f"{queue} has been drained!")
        # # Ignore the queue after draining
        # self.conn.ignore(queue)


if __name__ == "__main__":
    producer = JobProducer()
    producer.add_job_interactively()
