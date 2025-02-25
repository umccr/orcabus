import urllib.request
import logging
import os
from typing import Dict, Any, Optional, List
import gzip
import base64
import json
from libumccr.aws import libsm

logger = logging.getLogger(__name__)

class BSSHService:
    
    """Service class for BSSH (BaseSpace Sequence Hub) operations"""
    
    def __init__(self):
        assert os.environ.get("BASESPACE_ACCESS_TOKEN_SECRET_ID", None), "BASESPACE_ACCESS_TOKEN_SECRET_ID is not set"
        BASESPACE_ACCESS_TOKEN = libsm.get_secret(os.environ.get("BASESPACE_ACCESS_TOKEN_SECRET_ID"))
        if not BASESPACE_ACCESS_TOKEN:
            raise ValueError("BSSH_TOKEN is not set")
        self.headers = {
            'Authorization': f'Bearer {BASESPACE_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.aps2.sh.basespace.illumina.com/v2/"
        
    def get_run_details(self, api_url: str) -> Dict[str, Any]:
        """
        Retrieve run details from ICA API
        
        Args:
            api_url: Full API URL for the run (from BSSH event)
            
        Returns:
            Dict containing run details
        
        Example output of bssh run details api call:
        {
            "Id": "r.XXXXXXXXXXXX",
            "Name": "241024_A00130_0336_XXXXXXXXX",
            "ExperimentName": "241024_A00130_0336_XXXXXXXXX",
            "DateCreated": "2024-10-29T23:22:32.0000000Z",
            "DateModified": "2025-02-23T16:13:22.0000000Z",
            "Status": "Complete",
            "UserOwnedBy": {
                "Id": "0000000",
                "Href": "https://api.example.com/v2/users/0000000",
                "Name": "example_user",
                "DateCreated": "2024-04-16T01:57:41.0000000Z",
                "GravatarUrl": "https://secure.gravatar.com/avatar/xxxxx.jpg?s=20&d=mm&r=PG",
                "HrefProperties": "https://api.example.com/v2/users/current/properties",
                "ExternalDomainId": "XXXXXXXXXXXX"
            },
            "Instrument": {
                "Id": 1000000,
                "Name": "NovaSeq6000-simulator",
                "Number": 336,
                "Type": "NovaSeq6000",
                "PlatformName": "NovaSeq"
            },
            "InstrumentRunStatus": "Completed",
            "FlowcellBarcode": "XXXXXXXXX",
            "FlowcellPosition": "B",
            "LaneAndQcStatus": "QcPassed",
            "Workflow": "Generate FASTQ",
            "SampleSheetName": "SampleSheet.V2.XXXXXX.csv",
            "TotalSize": 1332913376661,
            "UserUploadedBy": {
                "Id": "0000000",
                "Name": "Example Name",
                // ... similar user fields as above ...
            },
            "UploadStatus": "Completed",
            "DateUploadStarted": "2024-10-29T23:22:33.0000000Z",
            "DateUploadCompleted": "2024-10-30T01:32:18.0000000Z",
            "IsArchived": false,
            "IsZipping": false,
            "IsZipped": false,
            "IsUnzipping": false,
            "Href": "https://api.example.com/v2/runs/0000000",
            "HrefFiles": "https://api.example.com/v2/runs/0000000/files",
            "HrefIcaUriFiles": "https://example.com/ica/link/project/xxxxx/data/xxxxx",
            "HasFilesInIca": true,
            "Properties": {
                "Items": [
                    {
                        "Type": "string[]",
                        "Name": "BaseSpace.LaneQcThresholds.1.Failed",
                        "Description": "The list of configured thresholds that were evaluated and failed",
                        "ContentItems": [],
                        "ItemsDisplayedCount": 0,
                        "ItemsTotalCount": 0
                    },
                    {
                        "Type": "string[]",
                        "Name": "BaseSpace.LaneQcThresholds.1.Passed",
                        "Description": "The list of configured thresholds that were evaluated and passed",
                        "ContentItems": ["Lane.PercentGtQ30"],
                        "ItemsDisplayedCount": 1,
                        "ItemsTotalCount": 1
                    },
                    // ... similar QC threshold entries for lanes 2-4 ...
                    {
                        "Type": "biosample[]",
                        "Name": "Input.BioSamples",
                        "Description": "",
                        "BioSampleItems": [
                            {
                                "Id": "0000000",
                                "BioSampleName": "LXXXXXXX",
                                "Status": "New",
                                "LabStatus": "Sequencing"
                                // ... other sample details ...
                            },
                            // ... more samples ...
                        ]
                    },
                    {
                        "Type": "library[]",
                        "Name": "Input.Libraries",
                        "Description": "",
                        "LibraryItems": [
                            {
                                "Id": "0000000",
                                "Name": "LXXXXXXX",
                                "Status": "Active"
                            }
                        ]
                    },
                    {
                        "Type": "librarypool[]",
                        "Name": "Input.LibraryPools",
                        "Description": "",
                        "LibraryPoolItems": [
                            {
                                "Id": "0000000",
                                "UserPoolId": "Pool_XXXXX_000",
                                "Status": "Active"
                                // ... other pool details ...
                            }
                        ]
                    }
                ]
            },
            "V1Pre3Id": "0000000"
        }
        """
        
        response = urllib.request.Request(api_url, headers=self.headers)
        with urllib.request.urlopen(response) as response:
            if response.status < 200 or response.status >= 300:
                raise ValueError(f'Non 20X status code returned')

            logger.info(f'Bssh run details api call successfully.')
            response_json = json.loads(response.read().decode())
            return response_json
    
    
    def get_libraries_from_run_details(self, run_details: Dict[str, Any]) -> List[str]:
        """
        Retrieve libraries names from run details
        """
        libraries = []
        for item in run_details.get('Properties', {}).get('Items', []):
            if item.get('Type') == 'library[]':
                libraries.extend([lib.get('Name') for lib in item.get('LibraryItems', [])])
        return libraries

    def get_sample_sheet(self, api_url: str, sample_sheet_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve sample sheet from ICA project
        
        Args:
            api_url: BSSH run URL
            sample_sheet_name: Name of the sample sheet file
            
        Returns:
            Base64 encoded gzip string containing sample sheet data or None if not found
            
        Example of run files api call response (api call to get files in project):
        {
            "Items": [
                {
                    "Id": "rXXXXXXX_XXXXXXXX",
                    "Href": "https://api.example.com/v2/files/XXXXX",
                    "HrefContent": "https://api.example.com/v2/files/XXXXX/content",
                    "Name": "SampleSheet.V2.XXXXX.csv",
                    "ContentType": "application/octet-stream",
                    "Size": 3662,
                    "Path": "SampleSheet.V2.XXXXX.csv",
                    "IsArchived": false,
                    "DateCreated": "2024-10-30T01:32:14.0000000Z",
                    "DateModified": "2024-10-30T01:32:14.0000000Z",
                    "ETag": "XXXXXXXXXXXXX"
                },
                {
                    "Id": "rXXXXXXX_XXXXXXXX",
                    "Name": "SampleSheet.V2.XXXXX.csv",
                    "... other fields same as above ...": ""
                },
                {
                    "Id": "rXXXXXXX_XXXXXXXX",
                    "Name": "SampleSheet.csv",
                    "... other fields same as above ...": ""
                }
            ],
            "Paging": {
                "DisplayedCount": 3,
                "Offset": 0,
                "Limit": 10,
                "SortDir": "Asc",
                "SortBy": "Id"
            }
        }
        
        """
        # Construct API URL for files in project
        bssh_run_files_url = f"{api_url}/files"
        
        try:
            file_content_url = None
            offset = 0
            limit = 100  # Assuming default limit is 100, adjust if different
            
            while True:
                params = {
                    'extension': 'csv',
                    'directory': '/',
                    'offset': offset,
                    'limit': limit
                }
                response = urllib.request.Request(bssh_run_files_url, headers=self.headers, params=params)
                with urllib.request.urlopen(response) as response:
                    if response.status < 200 or response.status >= 300:
                        raise ValueError(f'Non 20X status code returned when getting files in bssh run')

                    response_json = json.loads(response.read().decode())                    
                
                files = response_json.get('items', [])
                
                if not files:
                    break  # No more items to process
                
                # search the files for the sample sheet name
                for file in files:
                    if file['Name'] == sample_sheet_name:
                        file_content_url = file['HrefContent']
                        break
                
                if file_content_url:
                    break  # Found the file, exit loop
                
                # Check if we've received fewer items than limit (last page)
                if len(files) < limit:
                    break
                
                offset += limit  # Move to next page
                
            if not file_content_url:
                raise ValueError("Sample sheet not found")
            
            # Get file content
            response = urllib.request.Request(file_content_url, headers=self.headers)
            with urllib.request.urlopen(response) as response:
                if response.status < 200 or response.status >= 300:
                    raise ValueError(f'Non 20X status code returned when getting file content')

                logger.info(f'File content api call successfully.')
                response_json = json.loads(response.read().decode())
            
            # Get the raw content as bytes
            content = response.read()
            
            # Compress with gzip
            compressed = gzip.compress(content)
            
            # Encode to base64 and convert to string
            b64gz_string = base64.b64encode(compressed).decode('utf-8')
                
            return b64gz_string
            
        except Exception as e:
            raise ValueError(f"Error getting files in project: {e}")
    
    