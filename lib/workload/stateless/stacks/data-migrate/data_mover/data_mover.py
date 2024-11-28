import json
import logging
import os
import subprocess

import boto3
from mypy_boto3_stepfunctions import SFNClient


class DataMover:
    """
    A class to manage moving data.
    """

    def __init__(
        self,
        source: str,
        destination: str,
        repeat: int = 2,
        # 12 hours
        timeout: int = 43200,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self.source = source
        self.destination = destination
        self.repeat = repeat
        self.timeout = timeout
        self.logger = logger
        self.output = ""

    def sync(self):
        """
        Sync destination and source.
        """
        self.logger.info(
            f"syncing {self.repeat} times from {self.source} to {self.destination}"
        )

        out = None
        for _ in range(self.repeat):
            out = subprocess.run(
                ["aws", "s3", "sync", self.source, self.destination],
                check=True,
                # 1 day
                timeout=self.timeout,
            )
            self.logger.info(out.stdout)

            self.output += out.stdout or ""

        if out.stdout is not None:
            raise Exception("failed to sync - non-empty output")

    def delete(self):
        """
        Delete the source.
        """
        self.logger.info(f"deleting files from {self.source}")

        out = subprocess.run(
            ["aws", "s3", "rm", "--recursive", self.source],
            check=True,
            # 1 day
            timeout=self.timeout,
        )
        self.logger.info(out.stdout)

        self.output += out.stdout or ""

    def send_output(self):
        """
        Send successful task response with the output.
        """
        task_token = os.getenv("DM_TASK_TOKEN")
        if task_token is not None:
            client: SFNClient = boto3.client("stepfunctions")
            client.send_task_success(
                taskToken=task_token, output=json.dumps(self.output)
            )

    @staticmethod
    def send_failure(error: str):
        """
        Send a failed task response.
        """
        task_token = os.getenv("DM_TASK_TOKEN")
        if task_token is not None:
            client: SFNClient = boto3.client("stepfunctions")
            client.send_task_failure(taskToken=task_token, error=error)
