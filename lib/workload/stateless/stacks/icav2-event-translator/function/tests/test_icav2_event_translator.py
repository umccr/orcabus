import unittest
from botocore.session import Session
from botocore.stub import Stubber
import json
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Assuming you adapt your lambda function to use botocore for creating clients
from function.icav2_event_translator import handler, generate_icav2_internal_event, check_icav2_event  # Import your lambda function module

class TestICAv2EventTranslator(unittest.TestCase):
    def setUp(self):
        self.event = {
            "detail": {
                "projectId": "valid_project",
                "eventCode": "ICA_EXEC_028",
                "eventParameters": {
                    "analysisStatus": "SUCCEEDED"
                },
                "payload": {
                    "id": "valid_id",
                    "pipeline": {"id": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca"},
                    "userReference": "123456_A1234_0000_TestingPattern"
                }
            }
        }
        # Mock the environment variables
        os.environ['EVENT_BUS_NAME'] = 'test_event_bus'
        os.environ['TABLE_NAME'] = 'test_table'

        # Create a session and use it to create clients
        self.events = MagicMock()
        self.dynamodb = MagicMock()

        # Patch boto3 client and resource creation
        self.patch_client = patch('boto3.client', return_value=self.events)
        self.patch_resource = patch('boto3.resource', return_value={'Table': lambda x: self.dynamodb})
        self.patch_client.start()
        self.patch_resource.start()

        # Example of how to mock methods of these clients
        self.events.put_events = MagicMock(return_value={'Entries': [{'EventId': '1'}]})
        self.dynamodb.put_item = MagicMock(return_value={'ResponseMetadata': {'HTTPStatusCode': 200}})

    def tearDown(self):
        self.patch_client.stop()
        self.patch_resource.stop()

    def test_valid_event(self):
        # Create a valid test event
        event = {
            "detail": {
                "projectId": "valid_project",
                "eventCode": "ICA_EXEC_028",
                "eventParameters": {
                    "analysisStatus": "SUCCEEDED"
                },
                "payload": {
                    "id": "valid_id",
                    "pipeline": {"id": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca"},
                    "userReference": "123456_A1234_0000_TestingPattern"
                }
            }
        }
        context = {}

        # Execute the handler
        response = handler(event, context)

        # Assertions to check handler response and if the stubs were called correctly
        self.assertEqual(response['statusCode'], 200)
        self.events_stub.assert_no_pending_responses()
        self.dynamodb_stub.assert_no_pending_responses()

    def test_invalid_event(self):
        # Create an invalid test event
        event = {
            "detail": {
                "projectId": "invalid_project",
                "eventCode": "INVALID_CODE",
                "eventParameters": {
                    "analysisStatus": "FAILED"
                },
                "payload": {
                    "id": "invalid_id",
                    "pipeline": {"id": "wrong_id"},
                    "userReference": "wrong_reference"
                }
            }
        }
        context = {}

        # Execute the handler and expect it to raise a ValueError due to invalid conditions
        with self.assertRaises(ValueError):
            handler(event, context)

    def test_check_icav2_event_valid(self):
        # Execute & Assert
        self.assertTrue(check_icav2_event("ICA_EXEC_028", "SUCCEEDED", "bf93b5cf-cb27-4dfa-846e-acd6eb081aca", "123456_A1234_0000_TestingPattern"))

    def test_check_icav2_event_invalid(self):
        # Execute & Assert
        self.assertFalse(check_icav2_event("ICA_EXEC_029", "FAILED", "incorrect_id", "wrong_format"))
    
    def test_handler_no_eventbus_env(self):
        # Remove environment variable to test error handling
        del os.environ['EVENT_BUS_NAME']
        
        with self.assertRaises(AssertionError):
            handler(self.event, None)

    def test_handler_no_table_env(self):
        # Remove environment variable to test error handling
        del os.environ['TABLE_NAME']
        
        with self.assertRaises(AssertionError):
            handler(self.event, None)


