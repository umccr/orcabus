import urllib.request
import logging
import os
from typing import Dict, Any, Optional, List
import gzip
import base64
import json
from libumccr.aws import libsm
import requests

logger = logging.getLogger(__name__)

class BSSHService:
    
    """Service class for BSSH (BaseSpace Sequence Hub) operations"""
    
    def __init__(self):
        assert os.environ.get("BASESPACE_ACCESS_TOKEN_SECRET_ID", None), "BASESPACE_ACCESS_TOKEN_SECRET_ID is not set"
        try:
            BASESPACE_ACCESS_TOKEN = libsm.get_secret(os.environ.get("BASESPACE_ACCESS_TOKEN_SECRET_ID"))
        except Exception as e:
            logger.error(f"Error retrieving BSSH token from the Secret Manager: {e}")
            raise e
        
        if not BASESPACE_ACCESS_TOKEN:
            raise ValueError("BSSH_TOKEN is not set")
        self.headers = {
            'Authorization': f'Bearer {BASESPACE_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.aps2.sh.basespace.illumina.com/v2/"
        
    
    def handle_request_error(self, e: Exception, operation: str):
        """
        Handles various request exceptions and returns appropriate error
        
        Args:
            e: The caught exception
            operation: Description of the operation being performed
        """
        if isinstance(e, requests.exceptions.HTTPError):
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.reason}")
            logger.error(f"Response text: {e.response.text}")
            raise ValueError(f"Error {operation}: {str(e)}")
            
        elif isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            logger.error(f"Connection error occurred: {str(e)}")
            raise ValueError(f"Error connecting to BSSH: {str(e)}")
            
        elif isinstance(e, requests.exceptions.RequestException):
            logger.error(f"Request error occurred: {str(e)}")
            raise ValueError(f"Error making request to BSSH: {str(e)}")
            
        else:
            logger.error(f"Unexpected error: {str(e)}")
            raise ValueError(f"Unexpected error {operation}: {str(e)}")
        
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
                        "SampleLibraryItems": [
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
        
        try:
            response = requests.get(
                api_url,
                headers=self.headers
            )
            
            # Raise error for bad status codes
            response.raise_for_status()
            
            logger.info('BSSH run details API call successful.')
            return response.json()
            
        except Exception as e:
            self.handle_request_error(e, "getting run details")
    
    @staticmethod
    def get_libraries_from_run_details(run_details: Dict[str, Any]) -> List[str]:
        """
        Retrieve libraries names from run details
        """
        libraries = []
        for item in run_details.get('Properties', {}).get('Items', []):
            if item.get('Type') == 'library[]':
                libraries.extend([lib.get('Name') for lib in item.get('SampleLibraryItems', [])])
                break
        logger.info(f"Retrieved libraries: {libraries} from run details")
        return libraries

    def get_sample_sheet_from_bssh_run_files(self, api_url: str, sample_sheet_name: str) -> Optional[Dict[str, Any]]:
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
        
        logger.info(f'Bssh run files url: {bssh_run_files_url} , sample sheet name: {sample_sheet_name}')
        
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
                # Use requests library for the API call
                response = requests.get(
                    bssh_run_files_url,
                    params=params,  # requests will handle query parameter encoding
                    headers=self.headers
                )
                
                # Raise error for bad status codes
                response.raise_for_status()
                response_json = response.json()                   
                files = response_json.get('Items', [])
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
            
            logger.info(f'File content url: {file_content_url}')
            
            try:
                response = requests.get(
                    file_content_url,
                    headers=self.headers,
                    stream=True  # Important for binary content
                )
                response.raise_for_status()
                content = response.content
                
                if not content:
                    raise ValueError('Empty content received from BSSH')
                    
                logger.info(f'Successfully retrieved file content, size: {len(content)} bytes')
                
                # Convert to base64gz
                compressed_content = gzip.compress(content)
                b64gz_string = base64.b64encode(compressed_content).decode('utf-8')
                return b64gz_string
                    
            except Exception as e:
                self.handle_request_error(e, "getting sample sheet content")
            
        except Exception as e:
            self.handle_request_error(e, "getting sample sheet file")
    