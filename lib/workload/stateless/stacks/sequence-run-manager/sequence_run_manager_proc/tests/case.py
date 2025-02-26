import logging
import uuid
import os
from django.test import TestCase
from libumccr import aws
from libumccr.aws import libsqs, libeb, libsm
from mockito import when, unstub

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SequenceRunProcUnitTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        
        # Set AWS region
        os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"

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
        
        # Mock Secrets Manager client
        mock_sm = aws.client(
            "secretsmanager",
            endpoint_url="http://localhost:4566",
            region_name="ap-southeast-2",  # Use consistent region
            aws_access_key_id=str(uuid.uuid4()),
            aws_secret_access_key=str(uuid.uuid4()),
            aws_session_token=f"{uuid.uuid4()}_{uuid.uuid4()}",
        )
        when(aws).sm_client(...).thenReturn(mock_sm)
        when(libsm).sm_client(...).thenReturn(mock_sm)

    def tearDown(self) -> None:
        # Clean up environment variables
        if "BASESPACE_ACCESS_TOKEN_SECRET_ID" in os.environ:
            del os.environ["BASESPACE_ACCESS_TOKEN_SECRET_ID"]
        if "AWS_DEFAULT_REGION" in os.environ:
            del os.environ["AWS_DEFAULT_REGION"]
        unstub()

    def verify_local(self):
        queue_urls = libsqs.sqs_client().list_queues()["QueueUrls"]
        logger.info(f"SQS_QUEUE_URLS={queue_urls}")
        self.assertIn("4566", queue_urls[0])
        logger.info(f"-" * 32)


class SequenceRunProcIntegrationTestCase(TestCase):
    pass
