import logging
import uuid
import os
from django.test import TestCase
from libumccr import aws
from libumccr.aws import libsqs, libeb, libsm
from mockito import when, unstub, mock
from unittest.mock import patch

from sequence_run_manager_proc.services.bssh_srv import BSSHService
from sequence_run_manager_proc.tests.factories import SequenceRunManagerProcFactory

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
        
        os.environ["EVENT_BUS_NAME"] = "default"
        os.environ["BASESPACE_ACCESS_TOKEN_SECRET_ID"] = "test"
        os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2" 
        
        # Mock the libsm.get_secret function
        when(libsm).get_secret("test").thenReturn("mock-token")
    
        mock_run_details = SequenceRunManagerProcFactory.mock_bssh_run_details()
        mock_sample_sheet = SequenceRunManagerProcFactory.mock_bssh_sample_sheet()
        mock_bssh_service = mock(BSSHService)
        
        when(mock_bssh_service).get_run_details(...).thenReturn(mock_run_details)
        when(mock_bssh_service).get_sample_sheet_from_bssh_run_files(...).thenReturn(mock_sample_sheet)
        
        # Use patch to replace the BSSHService class with our mock
        patcher_seq = patch('sequence_run_manager_proc.services.sequence_srv.BSSHService', return_value=mock_bssh_service)
        patcher_lib = patch('sequence_run_manager_proc.services.sequence_library_srv.BSSHService', return_value=mock_bssh_service)
        patcher_sample_sheet = patch('sequence_run_manager_proc.services.sample_sheet_srv.BSSHService', return_value=mock_bssh_service)
        
        self.mock_bssh_class_lib = patcher_lib.start()
        self.mock_bssh_class_seq = patcher_seq.start()
        self.mock_bssh_class_sample_sheet = patcher_sample_sheet.start()
        self.addCleanup(patcher_lib.stop)
        self.addCleanup(patcher_seq.stop)
        self.addCleanup(patcher_sample_sheet.stop)

    def tearDown(self) -> None:
        # Clean up environment variables
        if "EVENT_BUS_NAME" in os.environ:
            del os.environ["EVENT_BUS_NAME"]
        if "BASESPACE_ACCESS_TOKEN_SECRET_ID" in os.environ:
            del os.environ["BASESPACE_ACCESS_TOKEN_SECRET_ID"]
        if "AWS_DEFAULT_REGION" in os.environ:
            del os.environ["AWS_DEFAULT_REGION"]
        if "AWS_ACCESS_KEY_ID" in os.environ:
            del os.environ["AWS_ACCESS_KEY_ID"]
        if "AWS_SECRET_ACCESS_KEY" in os.environ:
            del os.environ["AWS_SECRET_ACCESS_KEY"]
        if "AWS_SESSION_TOKEN" in os.environ:
            del os.environ["AWS_SESSION_TOKEN"]
            
        unstub()

    def verify_local(self):
        queue_urls = libsqs.sqs_client().list_queues()["QueueUrls"]
        logger.info(f"SQS_QUEUE_URLS={queue_urls}")
        self.assertIn("4566", queue_urls[0])
        logger.info(f"-" * 32)


class SequenceRunProcIntegrationTestCase(TestCase):
    pass
