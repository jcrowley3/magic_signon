import os
from urllib.parse import urlparse


class WorkerUtils:

    @staticmethod
    def build_job_payload(
        event_type: str,
        source: str,
        response_body: dict,
        response_tube: str = None,
        job_id: str = None,
        response_status: str = None,
    ):
        """Build the job payload for the worker to process."""

        return {
            "eventType": event_type,
            "source": source,
            "version": 0,
            "job_id": job_id,
            "response_tube": response_tube,
            "response_status": response_status,
            "body": response_body
        }

    @staticmethod
    def get_base_uri(url, env=None):
        """Get the base uri from the url. If the env is local, the base uri will be localstack:port"""

        parsed_url = urlparse(url)

        if env is None:
            env = os.environ.get("ENV", "local")

        if env == "local":
            base_uri = parsed_url.scheme + "://" + "localstack" + ":" + str(parsed_url.port)
        else:
            base_uri = parsed_url.scheme + "://" + parsed_url.netloc
        return base_uri

    @staticmethod
    def get_queue_name(queue_url: str) -> str:
        """Get the queue name from the queue url."""

        parsed_url = urlparse(queue_url)
        path_parts = parsed_url.path.split("/")
        last_part = path_parts[-1]

        last_part_split = last_part.split("-")
        queue_name = "-".join(last_part_split[1:]) if len(last_part_split) > 1 else last_part_split[0]

        return queue_name
