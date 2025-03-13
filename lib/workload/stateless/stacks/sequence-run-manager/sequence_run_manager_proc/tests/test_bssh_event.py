import os

from libumccr import libjson
from libumccr.aws import libssm, libeb
from mockito import when, verify

from sequence_run_manager.models.sequence import Sequence, SequenceStatus
from sequence_run_manager.models.state import State
from sequence_run_manager.models.sample_sheet import SampleSheet
from sequence_run_manager.tests.factories import TestConstant
from sequence_run_manager_proc.tests.factories import SequenceRunManagerProcFactory
from sequence_run_manager_proc.lambdas import bssh_event
from sequence_run_manager_proc.services.bssh_srv import BSSHService
from sequence_run_manager_proc.tests.case import logger, SequenceRunProcUnitTestCase
from sequence_run_manager_proc.domain.sequence import SequenceRuleError

"""
example event:
    {
    "version": "0",
    "id": f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454",  # Random UUID
    "detail-type": "Event from aws:sqs",
    "source": "Pipe IcaEventPipeConstru-xxxxxxxx",
    "account": "444444444444",
    "time": "2024-11-02T21:58:22Z",
    "region": "ap-southeast-2",
    "resources": [],
    "detail": {
        "ica-event": {
            "gdsFolderPath": "",
            "gdsVolumeName": "bssh.123456789fabcdefghijkl",
            "v1pre3Id": "444555555555",
            "dateModified": "2024-11-02T21:58:13.7451620Z",
            "acl": [
                "wid:12345678-debe-3f9f-8b92-21244f46822c",
                "tid:Yxmm......"
            ],
            "flowcellBarcode": "HVJJJJJJ",
            "icaProjectId": "12345678-53ba-47a5-854d-e6b53101adb7",
            "sampleSheetName": "SampleSheet.V2.134567.csv",
            "apiUrl": "https://api.aps2.sh.basespace.illumina.com/v2/runs/r.4Wz-ABCDEFGHIJKLM-A",
            "name": "222222_A01052_1234_BHVJJJJJJ",
            "id": "r.4Wz-ABCDEFGHIJKLMN-A",
            "instrumentRunId": "222222_A01052_1234_BHVJJJJJJ",
            "status": "New"
            }
        }
    }
"""

class BSSHEventUnitTests(SequenceRunProcUnitTestCase):
    def setUp(self) -> None:
        super(BSSHEventUnitTests, self).setUp()
        
    def tearDown(self) -> None:
        super(BSSHEventUnitTests, self).tearDown()
    #  comment as eventbridge rule will filter out unsupported event type
    # def test_unsupported_ens_event_type(self):
    #     """
    #     python manage.py test sequence_run_manager_proc.tests.test_bssh_event.BSSHEventUnitTests.test_unsupported_ens_event_type
    #     """
    #     ens_sqs_message_attributes = {
    #         "type": {
    #             "stringValue": "tes.runs",
    #             "stringListValues": [],
    #             "binaryListValues": [],
    #             "dataType": "String",
    #         },
    #         "producedby": {
    #             "stringValue": "BaseSpaceSequenceHub",
    #             "stringListValues": [],
    #             "binaryListValues": [],
    #             "dataType": "String",
    #         },
    #     }

    #     sqs_event_message = {
    #         "Records": [
    #             {
    #                 "eventSource": "aws:sqs",
    #                 "body": "does_not_matter",
    #                 "messageAttributes": ens_sqs_message_attributes,
    #             }
    #         ]
    #     }

    #     result = bssh_event.sqs_handler(sqs_event_message, None)
    #     self.assertIsNotNone(result)

    def test_event_handler(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_bssh_event.BSSHEventUnitTests.test_event_handler
        """
        when(libssm).get_ssm_param(...).thenReturn(libjson.dumps([]))

        _ = bssh_event.event_handler(SequenceRunManagerProcFactory.bssh_event_message(), None)

        qs = Sequence.objects.filter(
            sequence_run_id=TestConstant.sequence_run_id.value
        )
        seq = qs.get()
        logger.info(f"Found SequenceRun record from db: {seq}")
        self.assertEqual(1, qs.count())
        qs_states = State.objects.filter(sequence=seq)
        self.assertEqual(1, qs_states.count())
        verify(libeb, times=1).eb_client(...)  # event should fire
        
        # test event update
        _ = bssh_event.event_handler(SequenceRunManagerProcFactory.bssh_event_message('Complete'), None)
        
        qs = Sequence.objects.filter(
            sequence_run_id=TestConstant.sequence_run_id.value
        )
        seq = qs.get()
        logger.info(f"Found SequenceRun record from db: {seq}")
        self.assertEqual(SequenceStatus.SUCCEEDED, seq.status)
        qs_states = State.objects.filter(sequence=seq)
        self.assertEqual(2, qs_states.count())
        qs_sample_sheet = SampleSheet.objects.filter(sequence=seq)
        self.assertEqual(1, qs_sample_sheet.count())
        
        # clear db records
        qs_sample_sheet.delete()
        qs_states.delete()
        seq.delete()

    def test_event_handler_emergency_stop(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_bssh_event.BSSHEventUnitTests.test_event_handler_emergency_stop
        """
        # Mock emergency stop list to include our test run ID
        when(libssm).get_ssm_param(...).thenReturn(
            libjson.dumps([TestConstant.instrument_run_id.value])
        )

        # Test that SequenceRuleError logger is raised
        with self.assertLogs(logger, level='WARNING') as context:
            bssh_event.event_handler(SequenceRunManagerProcFactory.bssh_event_message(), None) # change status to complete

        # Verify the logging message
        self.assertIn("marked for emergency stop", str(context.output))

        # Verify sequence was still created
        qs = Sequence.objects.filter(
            instrument_run_id=TestConstant.instrument_run_id.value
        )
        sqr = qs.get()
        logger.info(f"Found SequenceRun record from db: {sqr}")
        self.assertEqual(1, qs.count())
        
        # Verify no event was emitted
        verify(libeb, times=0).eb_client(...)  # event should not fire
