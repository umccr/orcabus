import unittest
from unittest.mock import patch
import botocore.session
from botocore.stub import Stubber
import os
import json
from freezegun import freeze_time
from archive_service.universal_event_archiver import handler

class UniversalEventArchiverUnitTest(unittest.TestCase):
    def setUp(self):
        self.s3 = botocore.session.get_session().create_client('s3')
        self.stubber = Stubber(self.s3)
        self.stubber.activate()
        self.event = {
            "detail-type": "Test Event Type. ", # detail-type with withe space and special characters, testing sanitize_string
            "detail": {}
        }
        os.environ['BUCKET_NAME'] = 'test-bucket'
        patch('archive_service.universal_event_archiver.s3', self.s3).start()

    def tearDown(self):
        self.stubber.deactivate()
        patch.stopall()
        if 'BUCKET_NAME' in os.environ:
            del os.environ['BUCKET_NAME']

    # freeze time for time stamp testing purposes
    @freeze_time("2024-01-1")
    def test_handler_success(self):
        
        # expected time stamp (2024-01-01 00:00:00)
        expected_key = 'events/year=2024/month=01/day=01/Test_Event_Type_1704067200.0.json'
        expected_tagging = 'event_type=Test_Event_Type&event_time=2024-01-01__00-00-00'

        # Mock the response and setup stubbing
        response = {}
        expected_params = {
            'Bucket': 'test-bucket',
            'Key': expected_key,
            'Body': json.dumps(self.event),
            'Tagging': expected_tagging
        }
        self.stubber.add_response('put_object', response, expected_params)
        
        # Call the handler
        result = handler(self.event, None)
        
        # Verify
        self.assertEqual(result['statusCode'], 200)
        self.assertTrue('Event archived successfully!' in result['body'])
        self.stubber.assert_no_pending_responses()

    def test_handler_no_bucket_env(self):
        # Remove environment variable to test error handling
        del os.environ['BUCKET_NAME']
        
        with self.assertRaises(AssertionError):
            handler(self.event, None)
            