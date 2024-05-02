import json
import os
import datetime 
import unittest
import botocore.session
from botocore.stub import Stubber
from unittest.mock import patch
from freezegun import freeze_time

# Assuming you adapt your lambda function to use botocore for creating clients
from function.icav2_event_translator import handler, generate_icav2_internal_event, check_icav2_event  # Import your lambda function module

class TestICAv2EventTranslator(unittest.TestCase):
    def setUp(self):
        self.event = {
            "detail-type": "Test Event Type. ",
            "detail": {
                "projectId": "valid_project_id",
                "eventCode": "ICA_EXEC_028",
                "eventParameters": {
                    "analysisStatus": "SUCCEEDED"
                },
                "payload": {
                    "id": "valid_payload_id",
                    "pipeline": {"id": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca"},
                    "userReference": "123456_A1234_0000_TestingPattern"
                }
            }
        }
        # Mock the environment variables
        os.environ['EVENT_BUS_NAME'] = 'test_event_bus'
        os.environ['TABLE_NAME'] = 'test_table'

        
        # Create a session and use it to create clients
        self.events = botocore.session.get_session().create_client('events', region_name='ap-southeast-2')
        self.dynamodb = botocore.session.get_session().create_client('dynamodb', region_name='ap-southeast-2')
        self.events_stubber = Stubber(self.events)
        self.dynamodb_stubber = Stubber(self.dynamodb)
        self.events_stubber.activate()
        self.dynamodb_stubber.activate()
        patch('function.icav2_event_translator.events', self.events).start()
        patch('function.icav2_event_translator.dynamodb', self.dynamodb).start()

    def tearDown(self):
        self.events_stubber.deactivate()
        self.dynamodb_stubber.deactivate()
        patch.stopall()
        if 'EVENT_BUS_NAME' in os.environ:
            del os.environ['EVENT_BUS_NAME']
        if 'TABLE_NAME' in os.environ:
            del os.environ['TABLE_NAME']

    @freeze_time("2024-01-1")
    def test_valid_event(self):
        
        # expected internal event
        internal_event = {
            'project_id': "valid_project_id",
            'analysis_id': "valid_payload_id",
            'instrument_run_id': "123456_A1234_0000_TestingPattern",
            'tags': {
                'status': "",
                'payloadTags': {},
                'workflowSessionTags': {}
            }
        }
        
        # Mock the response and setup stubbing
        response = {}
        expected_params = {
            'Entries': [
                {
                    "Source": 'ocrabus.iet', # icav2 event translator
                    "DetailType": "ICAV2_INTERNAL_EVENT",
                    "Detail": json.dumps(internal_event),
                    "EventBusName": os.environ['EVENT_BUS_NAME']
                }
            ]
        }
        self.events_stubber.add_response('put_events', response, expected_params)
        
        #expected dynamodb table item
        expected_item = {
            'id': {'S': internal_event['analysis_id']},
            'id_type': {'S': 'icav2_analysis_id'},
            'original_external_event': {'S': json.dumps(self.event['detail'])},
            'translated_internal_event': {'S': json.dumps(internal_event)},
            'timestamp': {'S': datetime.datetime.now().isoformat()}
        }
        expected_params = {
            'Item':  expected_item,
            'TableName': 'test_table'
        }
        self.dynamodb_stubber.add_response('put_item', response, expected_params)
        
        # Execute the handler
        response = handler(self.event, None)

        # Assertions to check handler response and if the stubs were called correctly
        self.assertEqual(response['statusCode'], 200)
        self.events_stubber.assert_no_pending_responses()
        self.dynamodb_stubber.assert_no_pending_responses()

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


