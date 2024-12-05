import os

from libumccr import libjson
from libumccr.aws import libssm, libeb
from mockito import when, verify

from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.tests.factories import TestConstant
from sequence_run_manager_proc.lambdas import bssh_event
from sequence_run_manager_proc.tests.case import logger, SequenceRunProcUnitTestCase

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
            "status": "PendingAnalysis"
            }
        }
    }
"""

def bssh_event_message():
    mock_instrument_run_id = TestConstant.instrument_run_id.value
    mock_sequence_run_id = "r.ACGTlKjDgEy099ioQOeOWg"
    mock_sequence_run_name = mock_instrument_run_id
    mock_date_modified = "2020-05-09T22:17:03.1015272Z"
    mock_status = "PendingAnalysis"

    sequence_run_message = {
        "gdsFolderPath": f"/Runs/{mock_sequence_run_name}_{mock_sequence_run_id}",
        "gdsVolumeName": "bssh.acgtacgt498038ed99fa94fe79523959",
        "reagentBarcode": "NV9999999-ACGTA",
        "v1pre3Id": "666666",
        "dateModified": mock_date_modified,
        "acl": ["wid:e4730533-d752-3601-b4b7-8d4d2f6373de", "tid:Yxmm......"],
        "flowcellBarcode": "BARCODEEE",
        "icaProjectId": "12345678-53ba-47a5-854d-e6b53101adb7",
        "sampleSheetName": "MockSampleSheet.csv",
        "apiUrl": f"https://api.aps2.sh.basespace.illumina.com/v2/runs/{mock_sequence_run_id}",
        "name": mock_sequence_run_name,
        "id": mock_sequence_run_id,
        "instrumentRunId": mock_sequence_run_name,
        "status": mock_status,
    }

    orcabus_event_message = {
        "version": "0",
        "id": "f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454",  # Random UUID
        "detail-type": "Event from aws:sqs",
        "source": "Pipe IcaEventPipeConstru-xxxxxxxx",
        "account": "444444444444",
        "time": "2024-11-02T21:58:22Z",
        "region": "ap-southeast-2",
        "resources": [],
        "detail": {
            "ica-event": sequence_run_message,
        },
    }

    return orcabus_event_message


class BSSHEventUnitTests(SequenceRunProcUnitTestCase):
    def setUp(self) -> None:
        super(BSSHEventUnitTests, self).setUp()

        os.environ["EVENT_BUS_NAME"] = "default"

    def tearDown(self) -> None:
        super(BSSHEventUnitTests, self).tearDown()
        del os.environ["EVENT_BUS_NAME"]

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

        _ = bssh_event.event_handler(bssh_event_message(), None)

        qs = Sequence.objects.filter(
            instrument_run_id=TestConstant.instrument_run_id.value
        )
        seq = qs.get()
        logger.info(f"Found SequenceRun record from db: {seq}")
        self.assertEqual(1, qs.count())
        verify(libeb, times=1).eb_client(...)  # event should fire

    def test_event_handler_emergency_stop(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_bssh_event.BSSHEventUnitTests.test_event_handler_emergency_stop
        """
        when(libssm).get_ssm_param(...).thenReturn(
            libjson.dumps([TestConstant.instrument_run_id.value])
        )

        _ = bssh_event.event_handler(bssh_event_message(), None)

        qs = Sequence.objects.filter(
            instrument_run_id=TestConstant.instrument_run_id.value
        )
        sqr = qs.get()
        logger.info(f"Found SequenceRun record from db: {sqr}")
        self.assertEqual(1, qs.count())
        verify(libeb, times=0).eb_client(...)  # event should not fire
