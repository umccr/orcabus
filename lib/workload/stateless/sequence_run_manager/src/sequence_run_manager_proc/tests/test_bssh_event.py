import os

from libumccr import libjson
from libumccr.aws import libssm, libeb
from mockito import when, verify

from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.tests.factories import TestConstant
from sequence_run_manager_proc.lambdas import bssh_event
from sequence_run_manager_proc.tests.case import logger, SequenceRunProcUnitTestCase


def sqs_bssh_event_message():
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
        "acl": ["wid:e4730533-d752-3601-b4b7-8d4d2f6373de"],
        "flowcellBarcode": "BARCODEEE",
        "sampleSheetName": "MockSampleSheet.csv",
        "apiUrl": f"https://api.aps2.sh.basespace.illumina.com/v2/runs/{mock_sequence_run_id}",
        "name": mock_sequence_run_name,
        "id": mock_sequence_run_id,
        "instrumentRunId": mock_sequence_run_name,
        "status": mock_status,
    }

    ens_sqs_message_attributes = {
        "action": {
            "stringValue": "statuschanged",
            "stringListValues": [],
            "binaryListValues": [],
            "dataType": "String",
        },
        "actiondate": {
            "stringValue": "2020-05-09T22:17:10.815Z",
            "stringListValues": [],
            "binaryListValues": [],
            "dataType": "String",
        },
        "type": {
            "stringValue": "bssh.runs",
            "stringListValues": [],
            "binaryListValues": [],
            "dataType": "String",
        },
        "producedby": {
            "stringValue": "BaseSpaceSequenceHub",
            "stringListValues": [],
            "binaryListValues": [],
            "dataType": "String",
        },
        "contenttype": {
            "stringValue": "application/json",
            "stringListValues": [],
            "binaryListValues": [],
            "dataType": "String",
        },
    }

    sqs_event_message = {
        "Records": [
            {
                "eventSource": "aws:sqs",
                "body": libjson.dumps(sequence_run_message),
                "messageAttributes": ens_sqs_message_attributes,
                "attributes": {
                    "ApproximateReceiveCount": "3",
                    "SentTimestamp": "1589509337523",
                    "SenderId": "ACTGAGCTI2IGZA4XHGYYY:sender-sender",
                    "ApproximateFirstReceiveTimestamp": "1589509337535",
                },
                "eventSourceARN": "arn:aws:sqs:ap-southeast-2:843407916570:my-queue",
            }
        ]
    }

    return sqs_event_message


class BSSHEventUnitTests(SequenceRunProcUnitTestCase):
    def setUp(self) -> None:
        super(BSSHEventUnitTests, self).setUp()

        os.environ["EVENT_BUS_NAME"] = "default"

    def tearDown(self) -> None:
        super(BSSHEventUnitTests, self).tearDown()
        del os.environ["EVENT_BUS_NAME"]

    def test_unsupported_ens_event_type(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_bssh_event.BSSHEventUnitTests.test_unsupported_ens_event_type
        """
        ens_sqs_message_attributes = {
            "type": {
                "stringValue": "tes.runs",
                "stringListValues": [],
                "binaryListValues": [],
                "dataType": "String",
            },
            "producedby": {
                "stringValue": "BaseSpaceSequenceHub",
                "stringListValues": [],
                "binaryListValues": [],
                "dataType": "String",
            },
        }

        sqs_event_message = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": "does_not_matter",
                    "messageAttributes": ens_sqs_message_attributes,
                }
            ]
        }

        result = bssh_event.sqs_handler(sqs_event_message, None)
        self.assertIsNotNone(result)

    def test_sqs_handler(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_bssh_event.BSSHEventUnitTests.test_sqs_handler
        """
        when(libssm).get_ssm_param(...).thenReturn(libjson.dumps([]))

        _ = bssh_event.sqs_handler(sqs_bssh_event_message(), None)

        qs = Sequence.objects.filter(
            instrument_run_id=TestConstant.instrument_run_id.value
        )
        seq = qs.get()
        logger.info(f"Found SequenceRun record from db: {seq}")
        self.assertEqual(1, qs.count())
        verify(libeb, times=1).eb_client(...)  # event should fire

    def test_sqs_handler_emergency_stop(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_bssh_event.BSSHEventUnitTests.test_sqs_handler_emergency_stop
        """
        when(libssm).get_ssm_param(...).thenReturn(
            libjson.dumps([TestConstant.instrument_run_id.value])
        )

        _ = bssh_event.sqs_handler(sqs_bssh_event_message(), None)

        qs = Sequence.objects.filter(
            instrument_run_id=TestConstant.instrument_run_id.value
        )
        sqr = qs.get()
        logger.info(f"Found SequenceRun record from db: {sqr}")
        self.assertEqual(1, qs.count())
        verify(libeb, times=0).eb_client(...)  # event should not fire
