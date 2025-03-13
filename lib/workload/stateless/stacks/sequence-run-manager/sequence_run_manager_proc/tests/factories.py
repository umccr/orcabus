from sequence_run_manager.tests.factories import TestConstant

class SequenceRunManagerProcFactory:
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
    
    def mock_bssh_libraries():
        mock_libraries = [
            "L06789ABCD",
            "L01234ABCD",
        ]
        return mock_libraries

    def mock_bssh_sample_sheet():
        """example sample sheet content from 'v2-samplesheet-maker'"""
        mock_sample_sheet = """
            [Header]
            FileFormatVersion,2
            RunName,my-illumina-sequencing-run
            RunDescription,A test run
            InstrumentPlatform,NovaSeq 6000
            InstrumentType,NovaSeq

            [Reads]
            Read1Cycles,151
            Read2Cycles,151
            Index1Cycles,10
            Index2Cycles,10

            [BCLConvert_Settings]
            AdapterBehavior,trim
            BarcodeMismatchesIndex1,1
            BarcodeMismatchesIndex2,1
            MinimumAdapterOverlap,2
            OverrideCycles,Y151;Y10;Y8N2;Y151
            CreateFastqForIndexReads,False
            NoLaneSplitting,False
            FastqCompressionFormat,gzip

            [BCLConvert_Data]
            Lane,Sample_ID,index,index2,Sample_Project
            1,MyFirstSample,AAAAAAAAAA,CCCCCCCC,SampleProject
            1,MySecondSample,GGGGGGGGGG,TTTTTTTT,SampleProject""".strip()
        return mock_sample_sheet
    
    def mock_bssh_sample_sheet_dict():
        """mock sample sheet as a dictionary"""
        mock_sample_sheet = {
            "header": {
                "file_format_version": 2,
                "run_name": "my-illumina-sequencing-run",
                "run_description": "A test run",
                "instrument_platform": "NovaSeq 6000",
                "instrument_type": "NovaSeq",
            },
            "reads": {
                "read1_cycles": 151,
                "read2_cycles": 151,
                "index1_cycles": 10,
                "index2_cycles": 10,
            },
            "bclconvert_settings": {
                "adapter_behavior": "trim",
                "barcode_mismatches_index1": 1,
                "barcode_mismatches_index2": 1,
                "minimum_adapter_overlap": 2,
                "override_cycles": "Y151;Y10;Y8N2;Y151",
                "create_fastq_for_index_reads": False,
                "no_lane_splitting": False,
                "fastq_compression_format": "gzip",
            },
            "bclconvert_data": [
                {
                    "lane": 1,
                    "sample_id": "MyFirstSample",
                    "index": "AAAAAAAAAA",
                    "index2": "CCCCCCCC",
                    "sample_project": "SampleProject",
                },
                {
                    "lane": 1,
                    "sample_id": "MySecondSample",
                    "index": "GGGGGGGGGG",
                    "index2": "TTTTTTTT",
                    "sample_project": "SampleProject",
                },
            ]
        }

