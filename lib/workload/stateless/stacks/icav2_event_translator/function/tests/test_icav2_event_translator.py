import unittest
from unittest.mock import patch, MagicMock
import botocore.session
from botocore.stub import Stubber
import os

# Import lambda function modules
from function.icav2_event_translator import handler, generate_icav2_internal_event, check_icav2_event

class TestLambdaFunction(unittest.TestCase):

    def setUp(self):
        # set up mock event
        self.event = {
            "version": "0",
            "id": "cxxxx-xxx-xxxx-xxxx-xxxxxxx",
            "detail-type": "ICA_EXTERNAL_EVENT",
            "source": "my.source",
            "account": "12345678",
            "time": "2024-04-01T01:00:56Z",
            "region": "ap-southeast-2",
            "resources": [],
            "detail": {
                "projectId": "bxxx-xxxx-xxxx-xxx-xxxxxxxxx",
                "eventCode": "ICA_EXEC_028",
                "eventParameters": {
                    "analysisStatus": "SUCCEEDED"
                },
                "payload": {
                    "id": "0xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx",
                    "pipeline": {
                        "id": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca"
                    },
                    "userReference": "123456_A1234_0000_TestingPattern"
                }
            }
        }
        os.environ["EVENT_BUS_NAME"] = 'TestBus'
        os.environ["TABLE_NAME"] = 'TestTable'
        
    # def tearDown(self):
    #     self.eventbridge_stubber.deactivate()
    #     self.dynamodb_stubber.deactivate()
    #     self.patcher.stop()
        
    # def test_handler_success(self):
    #     # Execute
    #     response = handler(self.event, None)

    #     # Assert
    #     self.assertEqual(response['statusCode'], 200)

    def test_generate_icav2_internal_event(self, mock_generate):
        # Expected
        expected_internal_event = {
            "projectId": "bxxx-xxxx-xxxx-xxx-xxxxxxxxx",
            "analysisId": "0xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx",
            "instrumentRunId": "123456_A1234_0000",
            "tags": {}
        }
        
        # Execute
        result = generate_icav2_internal_event(self.event.get("detail",{}))

        # Assert
        self.assertEqual(result, expected_internal_event)

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
            handler(self.evnt, None)

    def test_handler_no_table_env(self):
        # Remove environment variable to test error handling
        del os.environ['TABLE_NAME']
        
        with self.assertRaises(AssertionError):
            handler(self.evnt, None)


