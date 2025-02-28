import os
from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.tests.factories import TestConstant, SequenceFactory
from sequence_run_manager_proc.domain.sequence import SequenceDomain
from sequence_run_manager_proc.services import sequence_srv
from sequence_run_manager_proc.tests.case import logger, SequenceRunProcUnitTestCase
from sequence_run_manager_proc.tests.test_bssh_event import mock_bssh_run_details
from sequence_run_manager_proc.services.bssh_srv import BSSHService
from mockito import when, mock
from libumccr.aws import libsm
from unittest.mock import patch

class SequenceRunSrvUnitTests(SequenceRunProcUnitTestCase):
    def setUp(self) -> None:
        super(SequenceRunSrvUnitTests, self).setUp()
        os.environ["BASESPACE_ACCESS_TOKEN_SECRET_ID"] = "test"
        os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"  # Add region
        
         # Mock the libsm.get_secret function
        when(libsm).get_secret("test").thenReturn("mock-token")
    
        #mock bssh service
        mock_run_details = mock_bssh_run_details()
        # Create a mock BSSHService
        mock_bssh_service = mock(BSSHService)
    
        # Mock the get_run_details method with any argument
        when(mock_bssh_service).get_run_details(any).thenReturn(mock_run_details)
    
        # Use patch to replace the BSSHService class with our mock
        patcher_lib = patch('sequence_run_manager_proc.services.sequence_library_srv.BSSHService', return_value=mock_bssh_service)
        patcher_seq = patch('sequence_run_manager_proc.services.sequence_srv.BSSHService', return_value=mock_bssh_service)
        self.mock_bssh_class_lib = patcher_lib.start()
        self.mock_bssh_class_seq = patcher_seq.start()
        self.addCleanup(patcher_lib.stop)
        self.addCleanup(patcher_seq.stop)

    def test_create_or_update_sequence_from_bssh_event(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_sequence_srv.SequenceRunSrvUnitTests.test_create_or_update_sequence_from_bssh_event
        """
        mock_payload = {
            "id": "r.ACGTlKjDgEy099ioQOeOWg",
            "name": TestConstant.instrument_run_id.value,
            "instrumentRunId": TestConstant.instrument_run_id.value,
            "dateModified": "2020-05-09T22:17:10.815Z",
            "status": "New",
            "gdsFolderPath": f"/Runs/{TestConstant.instrument_run_id.value}_r.ACGTlKjDgEy099ioQOeOWg",
            "gdsVolumeName": "bssh.dev",
            "reagentBarcode": "foo",
            "flowcellBarcode": "bar",
            "sampleSheetName": "SampleSheet.csv",
            "apiUrl": "https://bssh.dev/api/v1/runs/r.ACGTlKjDgEy099ioQOeOWg",
            'v1pre3Id': '1234567890',
            "acl": [
                "wid:12345678-debe-3f9f-8b92-21244f46822c",
                "tid:Yxmm......"
            ],
            "icaProjectId": "12345678-53ba-47a5-854d-e6b53101adb7",
        }
        seq_domain: SequenceDomain = (
            sequence_srv.create_or_update_sequence_from_bssh_event(mock_payload)
        )
        self.assertIsNotNone(seq_domain)
        logger.info(seq_domain)
        seq_in_db: Sequence = Sequence.objects.get(
            instrument_run_id=TestConstant.instrument_run_id.value
        )
        self.assertEqual(
            seq_domain.sequence.instrument_run_id, seq_in_db.instrument_run_id
        )
        self.assertTrue(
            seq_domain.status_has_changed
        )  # assert Sequence Run Status has changed True
        self.assertTrue(
            seq_domain.state_has_changed
        )  # assert Sequence Run State has changed True

        # assert status value are stored as upper case
        self.assertEqual(seq_in_db.status, "STARTED")

    def test_create_or_update_sequence_from_bssh_event_skip(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_sequence_srv.SequenceRunSrvUnitTests.test_create_or_update_sequence_from_bssh_event_skip
        """
        mock_seq: Sequence = SequenceFactory()
        seq_domain: SequenceDomain = (
            sequence_srv.create_or_update_sequence_from_bssh_event(
                {
                    "id": mock_seq.sequence_run_id,
                    "instrumentRunId": mock_seq.instrument_run_id,
                    "dateModified": mock_seq.start_time,
                    "gdsFolderPath": mock_seq.run_folder_path,
                    "gdsVolumeName": mock_seq.run_volume_name,
                    "status": "New",
                    'apiUrl': 'https://bssh.dev/api/v1/runs/r.ACGTlKjDgEy099ioQOeOWg',
                    'v1pre3Id': '1234567890',
                    "acl": [
                        "wid:12345678-debe-3f9f-8b92-21244f46822c",
                        "tid:Yxmm......"
                    ],
                    "icaProjectId": "12345678-53ba-47a5-854d-e6b53101adb7",
                }
            )
        )
        self.assertIsNotNone(seq_domain)
        self.assertEqual(1, Sequence.objects.count())
        self.assertFalse(
            seq_domain.status_has_changed
        )  # assert Sequence Run Status has changed False