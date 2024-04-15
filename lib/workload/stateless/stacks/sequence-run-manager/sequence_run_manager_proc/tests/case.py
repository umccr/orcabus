import logging
import uuid

from django.test import TestCase
from libumccr import aws
from libumccr.aws import libsqs, libeb
from mockito import when, unstub

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SequenceRunProcUnitTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()

        mock_sqs = aws.client(
            "sqs",
            endpoint_url="http://localhost:4566",
            region_name="us-east-1",
            aws_access_key_id=str(uuid.uuid4()),
            aws_secret_access_key=str(uuid.uuid4()),
            aws_session_token=f"{uuid.uuid4()}_{uuid.uuid4()}",
        )
        when(aws).sqs_client(...).thenReturn(mock_sqs)
        when(libsqs).sqs_client(...).thenReturn(mock_sqs)

        mock_eb = aws.client(
            "events",
            endpoint_url="http://localhost:4566",
            region_name="us-east-1",
            aws_access_key_id=str(uuid.uuid4()),
            aws_secret_access_key=str(uuid.uuid4()),
            aws_session_token=f"{uuid.uuid4()}_{uuid.uuid4()}",
        )
        when(aws).eb_client(...).thenReturn(mock_eb)
        when(libeb).eb_client(...).thenReturn(mock_eb)

    def tearDown(self) -> None:
        unstub()

    def verify_local(self):
        queue_urls = libsqs.sqs_client().list_queues()["QueueUrls"]
        logger.info(f"SQS_QUEUE_URLS={queue_urls}")
        self.assertIn("4566", queue_urls[0])
        logger.info(f"-" * 32)


class SequenceRunProcIntegrationTestCase(TestCase):
    pass
