import json
import os
import datetime 
import unittest
import botocore.session
from botocore.stub import Stubber
from unittest.mock import patch
from freezegun import freeze_time
from uuid import UUID
'''
{
    "portalRunId": "202405012397actg",
    "timestamp": "2024-05-01T09:25:44Z",
    "status": "succeeded",
    "workflowType": "bssh_bcl_convert",
    "workflowVersion": "4.2.7",
    "payload": {
      "refId": null,
      "version": "0.1.0",
      "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
      "analysisId": "aaaaafe8-238c-4200-b632-d5dd8c8db94a",
      "userReference": "540424_A01001_0193_BBBBMMDRX5_c754de_bd822f",
      "timeCreated": "2024-05-01T10:11:35Z",
      "timeModified": "2024-05-01T11:24:29Z",
      "pipelineId": "bfffffff-cb27-4dfa-846e-acd6eb081aca",
      "pipelineCode": "BclConvert v4_2_7",
      "pipelineDescription": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
      "pipelineUrn": "urn:ilmn:ica:pipeline:bfffffff-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7"
    },
    "serviceVersion": "0.1.0"
  }
'''

# Assuming you adapt your lambda function to use botocore for creating clients
from icav2_event_translator import handler  # Import your lambda function module

class TestICAv2EventTranslator(unittest.TestCase):
    def setUp(self):
        self.event = {
            "detail-type": "Test Event.",
            "detail": {
                'ica-event': { 
                    "projectId": "valid_project_id",
                    "eventCode": "ICA_EXEC_028",
                    "eventParameters": {
                        "analysisStatus": "SUCCEEDED"
                    },
                    "payload": {
                        "id": "valid_payload_id",
                        "userReference": "123456_A1234_0000_TestingPattern",
                        "timeCreated": "2024-01-01T00:11:35Z",
                        "timeModified": "2024-01-01T01:24:29Z",
                        "pipeline": {
                            "id": "valid_pipeline_id",
                            "code": "BclConvert v0_0_0",
                            "description": "This is an test autolaunch BclConvert pipeline.",
                            "urn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0"
                        },
                    }
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
        patch('icav2_event_translator.events', self.events).start()
        patch('icav2_event_translator.dynamodb', self.dynamodb).start()

    def tearDown(self):
        self.events_stubber.deactivate()
        self.dynamodb_stubber.deactivate()
        patch.stopall()
        if 'EVENT_BUS_NAME' in os.environ:
            del os.environ['EVENT_BUS_NAME']
        if 'TABLE_NAME' in os.environ:
            del os.environ['TABLE_NAME']

    
    @patch('icav2_event_translator.uuid4', return_value=UUID('12345678-1234-5678-1234-567812345678'))
    @freeze_time("2024-01-1")
    def test_valid_events_handler(self, mock_uuid4):
        # Your test code goes here
        
        response = {'Items': [], 'Count': 0, 'ScannedCount': 0}
        expected_params = {
            'TableName': 'test_table',
            'KeyConditionExpression': 'id = :analysis_id and id_type = :id_type',
            'ExpressionAttributeValues': {':analysis_id': {'S': 'valid_payload_id'}, ':id_type': {'S': 'analysis_id'}}
        }
        self.dynamodb_stubber.add_response('query', response, expected_params)
        
        response = {}
        expected_params = {
            'TableName': 'test_table',
            'Item':{
                'id': {'S': 'valid_payload_id'},
                'id_type': {'S': 'analysis_id'},
                "portal_run_id": {'S': '2024010112345678'}
              }
         }
        self.dynamodb_stubber.add_response('put_item', response, expected_params)
        expected_params = {
            'TableName': 'test_table',
            'Item':{
                'id': {'S': '2024010112345678'},
                'id_type': {'S': 'portal_run_id'},
                "analysis_id": {'S': 'valid_payload_id'}
              }
         }
        self.dynamodb_stubber.add_response('put_item', response, expected_params)
        
        # expected internal event
        expected_ica_event_details = {
            "portalRunId": '2024010112345678',
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "status": "SUCCEEDED",
            "workflowType": "bssh_bcl_convert",
            "workflowVersion": "4.2.7",
            "payload": {
                "refId": None,
                "version": "0.1.0",
                "projectId": "valid_project_id",
                "analysisId": "valid_payload_id",
                "userReference": "123456_A1234_0000_TestingPattern",
                "timeCreated": "2024-01-01T00:11:35Z",
                "timeModified": "2024-01-01T01:24:29Z",
                "pipelineId": "valid_pipeline_id",
                "pipelineCode": "BclConvert v0_0_0",
                "pipelineDescription": "This is an test autolaunch BclConvert pipeline.",
                "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0"
            }
        }
        
        # Mock the response and setup stubbing
        response = {}
        expected_params = {
            'Entries': [
                {
                    "Source": "orcabus.bcm",
                    "DetailType": "WorkflowRunStateChange",
                    "Detail": json.dumps(expected_ica_event_details),
                    "EventBusName": os.environ['EVENT_BUS_NAME']
                }
            ]
        }
        self.events_stubber.add_response('put_events', response, expected_params)
        
        
        # expected dynamodb table item
        expected_item = {
            'id': {'S': '12345678-1234-5678-1234-567812345678'},
            'id_type': {'S': 'db_uuid'},
            'analysis_id': {'S': expected_ica_event_details['payload']['analysisId']},
            'analysis_status': {'S': 'SUCCEEDED'},
            "portal_run_id": {'S': expected_ica_event_details['portalRunId']},
            'original_external_event': {'S': json.dumps(self.event['detail']['ica-event'])},
            'translated_internal_ica_event': {'S': json.dumps(expected_ica_event_details)},
            'timestamp': {'S': expected_ica_event_details['timestamp']}
        }
        expected_params = {
            'Item':  expected_item,
            'TableName': 'test_table'
        }
        self.dynamodb_stubber.add_response('put_item', response, expected_params)
        
        expected_params= {
            'TableName': 'test_table',
            'Key': {
                'id': {'S': "valid_payload_id"},
                'id_type': {'S': 'analysis_id'}
            },
            'UpdateExpression': 'SET db_uuid = :db_uuid',
            'ExpressionAttributeValues': {
            ':db_uuid': {'S': '12345678-1234-5678-1234-567812345678'}
            }
        }
        self.dynamodb_stubber.add_response('update_item', response, expected_params)
        
        expected_params= {
            'TableName': 'test_table',
            'Key': {
                'id': {'S': '2024010112345678'},
                'id_type': {'S': 'portal_run_id'}
            },
            'UpdateExpression': 'SET db_uuid = :db_uuid',
            'ExpressionAttributeValues': {
            ':db_uuid': {'S': '12345678-1234-5678-1234-567812345678'}
            }
        }
        self.dynamodb_stubber.add_response('update_item', response, expected_params)
        
        # Execute the handler
        response = handler(self.event, None)

        # Assertions to check handler response and if the stubs were called correctly
        self.assertEqual(response['statusCode'], 200)
        self.events_stubber.assert_no_pending_responses()
        self.dynamodb_stubber.assert_no_pending_responses()
    
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


