import json
import os
import unittest
import botocore.session
from botocore.stub import Stubber
from unittest.mock import patch
from freezegun import freeze_time

'''
assume output event is in the following format:
(Non-SUCCEEDED Event without payload)
{
    "portalRunId": "2024010112345678",
    "executionId": "valid_payload_id",
    "timestamp": "2024-00-25T00:07:00Z",
    "status": "FAILED", (Non-SUCCEEDED status)
    "workflowName": "BclConvert",
    "workflowVersion": "4.2.7",
    workflowRunName: "123456_A1234_0000_TestingPattern",
}

(SUCCEEDED Event)
{
    "portalRunId": "2024010112345678",
    "executionId": "valid_payload_id",
    "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "status": "SUCCEEDED",
    "workflowName":"BclConvert",
    "workflowVersion": "0.0.0",
    "workflowRunName": "123456_A1234_0000_TestingPattern",
    "payload": {
        "version": "0.1.0",
        "data": {
            "projectId": "valid_project_id",
            "analysisId": "valid_payload_id",
            "userReference": "123456_A1234_0000_TestingPattern",
            "timeCreated": "2024-01-01T00:11:35Z",
            "timeModified": "2024-01-01T01:24:29Z",
            "pipelineId": "valid_pipeline_id",
            "pipelineCode": "BclConvert v0_0_0",
            "pipelineDescription": "This is an test autolaunch BclConvert pipeline.",
            "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0"
            "instrumentRunId": "12345_A12345_1234_ABCDE12345",
            "basespaceRunId": "1234567",
            "samplesheetB64gz": "test_sample_sheetB64gz"
        }
    }
  }
'''

# Assuming you adapt your lambda function to use botocore for creating clients
from icav2_event_translator import handler  # Import lambda function module

def mock_collect_analysis_objects():
    return {
        "instrument_run_id": "12345_A12345_1234_ABCDE12345",
        "basespace_run_id": "1234567",
        "samplesheet_b64gz":"test_samplesheet_b64gz"
    }

def mock_generate_db_uuid():
    return {
        "db_uuid": "12345678-1234-5678-1234-567812345678"
    }

class TestICAv2EventTranslator(unittest.TestCase):
    def setUp(self):
        self.test_event = {
            "detail-type": "Test Event.",
            "detail": {
                'ica-event': { 
                    "projectId": "valid_project_id",
                    "eventCode": "ICA_EXEC_028",
                    "eventParameters": {
                        "analysisStatus": "UNSPECIFIED"
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
        os.environ['ICAV2_BASE_URL'] = 'https://test.com'
        os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = 'test_secret_id'

        
        # Create a session and use it to create clients
        self.events = botocore.session.get_session().create_client('events', region_name='ap-southeast-2')
        self.dynamodb = botocore.session.get_session().create_client('dynamodb', region_name='ap-southeast-2')
        self.events_stubber = Stubber(self.events)
        self.dynamodb_stubber = Stubber(self.dynamodb)
        self.events_stubber.activate()
        self.dynamodb_stubber.activate()
        
        # start all patches
        patches = [
            patch('icav2_event_translator.events', self.events),
            patch('icav2_event_translator.dynamodb', self.dynamodb),
            patch('icav2_event_translator.generate_db_uuid', return_value=mock_generate_db_uuid()),
            patch('icav2_event_translator.generate_portal_run_id', return_value='2024010112345678'),
            patch('icav2_event_translator.set_icav2_env_vars', return_value=None),
            patch('icav2_event_translator.collect_analysis_objects', return_value=mock_collect_analysis_objects())
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
            
    def tearDown(self):
        self.events_stubber.deactivate()
        self.dynamodb_stubber.deactivate()
        patch.stopall()
        self.cleanup_environment_vars()
    
    def test_succeeded_event(self):
        self.setup_event("SUCCEEDED")
        self.setup_expected_ica_event_details("SUCCEEDED")
        self.run_event_test()

    def test_progress_event(self):
        self.setup_event("INPROGRESS")
        self.setup_expected_ica_event_details("INPROGRESS")
        self.run_event_test()
    
    def setup_event(self, status):
        """
        Set up expected ICA event details based on the given status.
    
        :param status: A string representing the status of the event ('SUCCEEDED' or any non-success status).
        """
        self.test_event['detail']['ica-event']['eventParameters']['analysisStatus'] = status
    
    def setup_expected_ica_event_details(self, status):
        """
        Set up expected ICA event details based on the given status.
    
        :param status: A string representing the status of the event ('SUCCEEDED' or any non-success status).
        """
        # Basic event details that are common to all statuses
        self.expected_ica_event_details = {
            "portalRunId": '2024010112345678',
            "executionId": "valid_payload_id",
            "timestamp": "2024-01-01T00:00:00Z",
            "status": status,
            "workflowName": "BclConvert",
            "workflowVersion": "0.0.0",
            "workflowRunName": "123456_A1234_0000_TestingPattern"
        }

    # Add payload details only if the status is "SUCCEEDED"
        if status == "SUCCEEDED":
            self.expected_ica_event_details["payload"] = {
                "version": "0.1.0",
                "data": {
                    "projectId": "valid_project_id",
                    "analysisId": "valid_payload_id",
                    "userReference": "123456_A1234_0000_TestingPattern",
                    "timeCreated": "2024-01-01T00:11:35Z",
                    "timeModified": "2024-01-01T01:24:29Z",
                    "pipelineId": "valid_pipeline_id",
                    "pipelineCode": "BclConvert v0_0_0",
                    "pipelineDescription": "This is an test autolaunch BclConvert pipeline.",
                    "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0",
                    "instrumentRunId": "12345_A12345_1234_ABCDE12345",
                    "basespaceRunId": "1234567",
                    "samplesheetB64gz": "test_samplesheet_b64gz"
                }
            }
        
    @freeze_time("2024-01-1")
    def run_event_test(self):
        """
        Arrange: stub responses in the order they are expected to be called
        1. dynamodb.query
        2. dynamodb.put_item
        3. dynamodb.put_item
        4. events.put_events
        5. dynamodb.put_item
        6. dynamodb.update_item
        7. dynamodb.update_item
        """
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
        expected_ica_event_details = self.expected_ica_event_details
        # Mock the response and setup stubbing
        response = {}
        expected_params = {
            'Entries': [
                {
                    "Source": "orcabus.bclconvertmanager",
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
            'analysis_id': {'S': "valid_payload_id"},
            'analysis_status': {'S': expected_ica_event_details['status']},
            "portal_run_id": {'S': expected_ica_event_details['portalRunId']},
            'original_external_event': {'S': json.dumps(self.test_event['detail']['ica-event'])},
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
        response = handler(self.test_event, None)

        # Assertions to check handler response and if the stubs were called correctly
        self.assertEqual(response['statusCode'], 200)
        self.events_stubber.assert_no_pending_responses()
        self.dynamodb_stubber.assert_no_pending_responses()
    
    def test_missing_environment_variables(self):
        # Remove environment variable to test error handling
        del os.environ['EVENT_BUS_NAME']
        with self.assertRaises(AssertionError):
            handler(self.test_event, None)
        # Reset for next test
        os.environ['EVENT_BUS_NAME'] = 'test_event_bus'
        
        # Remove environment variable to test error handling
        del os.environ['TABLE_NAME']
        with self.assertRaises(AssertionError):
            handler(self.test_event, None)
        # Reset for next test
        os.environ['TABLE_NAME'] = 'test_table'
        
        # Test missing ICAV2_BASE_URL
        del os.environ['ICAV2_BASE_URL']
        with self.assertRaises(AssertionError):
            handler(self.test_event, None)
        # Reset for next test
        os.environ['ICAV2_BASE_URL'] = 'https://test.com'

        # Test missing ICAV2_ACCESS_TOKEN_SECRET_ID
        del os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID']
        with self.assertRaises(AssertionError):
            handler(self.test_event, None)
        # Reset for next test
        os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = 'test_secret_id'
        
    def cleanup_environment_vars(self):
        del os.environ['EVENT_BUS_NAME']
        del os.environ['TABLE_NAME']
        del os.environ['ICAV2_BASE_URL']
        del os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID']
    


