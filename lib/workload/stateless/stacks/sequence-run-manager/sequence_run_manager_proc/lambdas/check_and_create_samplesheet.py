import os
import logging

import django

django.setup()

from typing import Dict, List
import json
import boto3
from django.utils import timezone
from django.db import transaction
from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.models.sample_sheet import SampleSheet

# Configure logging for AWS Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ASSOCIATION_STATUS = "ACTIVE"

class SampleSheetProcessor:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.stats = {
            "processed_count": 0,
            "error_count": 0,
            "success_count": 0,
            "skipped_count": 0,
            "total_associations_created": 0
        }
        self.sequence_cache = {}
        
    def prefetch_sequences(self, orcabus_ids: List[str]):
        """Prefetch sequences for all instrument IDs"""
        sequences = Sequence.objects.filter(orcabus_id__in=orcabus_ids)
        self.sequence_cache = {seq.orcabus_id: seq for seq in sequences}
        logger.info(f"Prefetched {len(self.sequence_cache)} sequences")
    
        
    def process_file(self, data: List[Dict]) -> List[Dict]:
        """Process all records in the file"""
        logger.info(f"Starting to process {len(data)} records")
        
        orcabus_ids = [record['orcabus_id'].split('.')[1] for record in data]
        self.prefetch_sequences(orcabus_ids)
        
        results = []
        
        samplesheet_to_create = []
        for record in data:
            result = {
                "orcabus_id": record['orcabus_id'],
                "status": "success"
            }
            try:
                sequence = self.sequence_cache.get(record['orcabus_id'])
                if not sequence:
                    result.update({
                        "status": "error",
                        "error": "Sequence not found"
                    })
                    self.stats["error_count"] += 1
                    results.append(result)
                    continue
                
                samplesheet_to_create.append(SampleSheet(
                    sequence=sequence,
                    sample_sheet_name=record['sample_sheet_name'],
                    association_status=ASSOCIATION_STATUS,
                    sample_sheet_content=record['sample_sheet_content'],
                    association_timestamp=timezone.now()
                ))
                
                self.stats["success_count"] += 1
                results.append(result)
            except Exception as e:
                result.update({
                    "status": "error",
                    "error": str(e)
                })
                self.stats["error_count"] += 1
                results.append(result)
        
        if samplesheet_to_create:
            with transaction.atomic():
                SampleSheet.objects.bulk_create(samplesheet_to_create)
                self.stats["total_associations_created"] += len(samplesheet_to_create)
                logger.info(f"Created {len(samplesheet_to_create)} samplesheets")
        
        return results
        


def handler(event, context):
    """
    Lambda handler for processing library linking file
    
    Expected event structure:
    {
        "key": "sequence_samplesheet_linking.json"
    }
    
    file data format:
    [
        {
            "orcabus_id": "seq.0123456789",
            "instrument_run_id": "2222222_A111111_0000_ABCDEFGH",
            "sample_sheet_name": "samplesheet-123456789.csv",
            "sample_sheet_content": {
                "header": {
                    "file_format_version": 2,
                    "run_name": "RUN_NAME",
                    "instrument_type": "INSTRUMENT_TYPE"
                },
                "data": [
                    {
                        "sample_name": "SAMPLE_NAME",
                        "sample_id": "SAMPLE_ID",
                        "sample_type": "SAMPLE_TYPE",
                    }
                ]
                ...
            }
        },
    ...
    ]
    """
    
    processor = SampleSheetProcessor()
    
    assert os.environ['LINKING_DATA_BUCKET_NAME'], "LINKING_DATA_BUCKET_NAME is not set"

    try:
        # Read data from S3
        response = processor.s3_client.get_object(
            Bucket=os.environ['LINKING_DATA_BUCKET_NAME'],
            Key=event['key']
        )
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Process the file
        results = processor.process_file(data)
        
        # Prepare summary
        summary = {
            "file_processed": event['key'],
            "total_records": len(data),
            **processor.stats,
            "total_associations": processor.stats["total_associations_created"],
            "completed": processor.stats["processed_count"] == len(data),
            "results": results
        }
        
        logger.info(f"Processing summary: {summary}")
        
        return {
            "statusCode": 200,
            "body": json.dumps(summary)
        }
            
    except Exception as e:
        logger.error(f"Fatal error processing file {event['key']}: {str(e)}")
        raise