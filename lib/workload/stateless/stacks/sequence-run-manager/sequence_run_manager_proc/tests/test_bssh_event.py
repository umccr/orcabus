import os

from libumccr import libjson
from libumccr.aws import libssm, libeb, libsm
from mockito import when, verify, mock
from unittest.mock import patch

from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.tests.factories import TestConstant
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

def bssh_event_message(mock_run_status: str = "New"):
    mock_sequence_run_id = TestConstant.sequence_run_id.value
    mock_sequence_run_name = mock_sequence_run_id
    mock_date_modified = "2020-05-09T22:17:03.1015272Z"
    mock_status = mock_run_status
    mock_instrument_run_id = TestConstant.instrument_run_id.value

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
        "instrumentRunId": mock_instrument_run_id,
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

def mock_bssh_run_details():
    mock_run_details = {
            "Id": "r.ACGTlKjDgEy099ioQOeOWg",
            "Name": "241024_A00130_0336_00000000",
            "ExperimentName": "ExperimentName",
            "DateCreated": "2024-10-29T23:22:32.0000000Z",
            "DateModified": "2025-02-23T16:13:22.0000000Z",
            "Status": "Complete",
            "UserOwnedBy": { # omit other fields here
                "Id": "0000000", 
            },
            "Instrument": { # omit other fields here
                "Id": 1000000, 
                "Name": "NovaSeq6000-simulator",
            },
            "InstrumentRunStatus": "Completed",
            "FlowcellBarcode": "BARCODEEE",
            "FlowcellPosition": "B",
            "LaneAndQcStatus": "QcPassed",
            "Workflow": "Generate FASTQ",
            "SampleSheetName": "SampleSheet.V2.XXXXXX.csv",
            "TotalSize": 1332913376661,
            "UserUploadedBy": { # omit other fields here
                "Id": "0000000",
                "Name": "Example Name",
            },
            "UploadStatus": "Completed",
            "DateUploadStarted": "2024-10-29T23:22:33.0000000Z",
            "DateUploadCompleted": "2024-10-30T01:32:18.0000000Z",
            "IsArchived": False,
            "IsZipping": False,
            "IsZipped": False,
            "IsUnzipping": False,
            "Href": "https://api.example.com/v2/runs/0000000",
            "HrefFiles": "https://api.example.com/v2/runs/0000000/files",
            "HrefIcaUriFiles": "https://example.com/ica/link/project/xxxxx/data/xxxxx",
            "HasFilesInIca": True,
            "Properties": {
                "Items": [
                    {
                        "Type": "string[]",
                        "Name": "BaseSpace.LaneQcThresholds.1.Failed",
                        "Description": "The list of configured thresholds that were evaluated and failed",
                        "ContentItems": [],
                        "ItemsDisplayedCount": 0,
                        "ItemsTotalCount": 0
                    },# omit other fields here
                    
                    {
                        "Type": "biosample[]",
                        "Name": "Input.BioSamples",
                        "Description": "",
                        "BioSampleItems": [
                            { # omit other fields here
                                "Id": "0000000",
                                "BioSampleName": "LXXXXXXX",
                                "Status": "New",
                                "LabStatus": "Sequencing"
                            },
                        ]
                    },
                    {
                        "Type": "library[]",
                        "Name": "Input.Libraries",
                        "Description": "",
                        "LibraryItems": [
                            { # omit other fields here
                                "Id": "0000000",
                                "Name": "L06789ABCD",
                                "Status": "Active"
                            },
                            { # omit other fields here
                                "Id": "1111111111",
                                "Name": "L01234ABCD",
                                "Status": "Active"
                            }
                        ]
                    },
                    {
                        "Type": "librarypool[]",
                        "Name": "Input.LibraryPools",
                        "Description": "",
                        "LibraryPoolItems": [
                            { # omit other fields here
                                "Id": "0000000",
                                "UserPoolId": "Pool_XXXXX_000",
                                "Status": "Active"
                            }
                        ]
                    }
                ]
            },
            "V1Pre3Id": "1234567890"
        }
    return mock_run_details


class BSSHEventUnitTests(SequenceRunProcUnitTestCase):
    def setUp(self) -> None:
        super(BSSHEventUnitTests, self).setUp()

        os.environ["EVENT_BUS_NAME"] = "default"
        os.environ["BASESPACE_ACCESS_TOKEN_SECRET_ID"] = "test"
        os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2" 
        
        # Mock the libsm.get_secret function
        when(libsm).get_secret("test").thenReturn("mock-token")
    
        mock_run_details = mock_bssh_run_details()
        mock_bssh_service = mock(BSSHService)
        
        when(mock_bssh_service).get_run_details(...).thenReturn(mock_run_details)
        
        # Use patch to replace the BSSHService class with our mock
        patcher_lib = patch('sequence_run_manager_proc.services.sequence_library_srv.BSSHService', return_value=mock_bssh_service)
        patcher_seq = patch('sequence_run_manager_proc.services.sequence_srv.BSSHService', return_value=mock_bssh_service)
        
        self.mock_bssh_class_lib = patcher_lib.start()
        self.mock_bssh_class_seq = patcher_seq.start()
        self.addCleanup(patcher_lib.stop)
        self.addCleanup(patcher_seq.stop)
        
    def tearDown(self) -> None:
        # Safely remove environment variables if they exist
        if "EVENT_BUS_NAME" in os.environ:
            del os.environ["EVENT_BUS_NAME"]
        if "BASESPACE_ACCESS_TOKEN_SECRET_ID" in os.environ:
            del os.environ["BASESPACE_ACCESS_TOKEN_SECRET_ID"]
        
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

        _ = bssh_event.event_handler(bssh_event_message(), None)

        qs = Sequence.objects.filter(
            sequence_run_id=TestConstant.sequence_run_id.value
        )
        seq = qs.get()
        logger.info(f"Found SequenceRun record from db: {seq}")
        self.assertEqual(1, qs.count())
        verify(libeb, times=1).eb_client(...)  # event should fire

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
            bssh_event.event_handler(bssh_event_message('Complete'), None) # change status to complete

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
