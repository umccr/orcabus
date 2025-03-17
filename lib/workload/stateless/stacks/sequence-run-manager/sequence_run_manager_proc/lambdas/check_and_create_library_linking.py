import os
import logging

import django

django.setup()

from typing import Dict, List
import time
import json
import boto3
from django.utils import timezone
from django.db import transaction
from sequence_run_manager.models.sequence import Sequence, LibraryAssociation

# Configure logging for AWS Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants - Optimized for files with <200 records
BATCH_SIZE = 50  # Keep bulk create batch size for database operations
ASSOCIATION_STATUS = "ACTIVE"

class LibraryLinkingProcessor:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.start_time = time.time()
        self.stats = {
            "processed_count": 0,
            "error_count": 0,
            "success_count": 0,
            "skipped_count": 0,
            "total_associations_created": 0
        }
        self.sequence_cache = {}
        
    
        
    def prefetch_sequences(self, instrument_ids: List[str]):
        """Prefetch sequences for all instrument IDs"""
        sequences = Sequence.objects.filter(instrument_run_id__in=instrument_ids)
        self.sequence_cache = {seq.instrument_run_id: seq for seq in sequences}
        logger.info(f"Prefetched {len(self.sequence_cache)} sequences")
        
    def check_existing_associations(self, sequence_ids: List[str]) -> set:
        """Get sequences that already have associations"""
        existing = LibraryAssociation.objects.filter(
            sequence_id__in=sequence_ids
        ).values_list('sequence_id', flat=True)
        return set(existing)
        
    def process_batch(self, records: List[Dict], batch_index: int) -> List[Dict]:
        """Process a batch of records efficiently"""
        results = []
        
        # Prefetch sequences for all records at once
        instrument_ids = [record['instrument_id'] for record in records]
        self.prefetch_sequences(instrument_ids)
        
        # Check existing associations in one query
        sequence_ids = [seq.orcabus_id for seq in self.sequence_cache.values()]
        existing_associations = self.check_existing_associations(sequence_ids)
        
        # Process records
        associations_to_create = []
        
        for record in records:
            instrument_id = record['instrument_id']
            result = {
                "instrument_id": instrument_id,
                "batch_index": batch_index
            }
            
            try:
                sequence = self.sequence_cache.get(instrument_id)
                if not sequence:
                    result.update({
                        "status": "error",
                        "error": "Sequence not found"
                    })
                    self.stats["error_count"] += 1
                    results.append(result)
                    continue
                
                if sequence.orcabus_id in existing_associations:
                    result.update({
                        "status": "skipped",
                        "reason": "existing_associations"
                    })
                    self.stats["skipped_count"] += 1
                    results.append(result)
                    continue
                
                # Collect all associations for bulk create
                associations_to_create.extend([
                    LibraryAssociation(
                        library_id=library_id,
                        sequence=sequence,
                        association_date=timezone.now(),
                        status=ASSOCIATION_STATUS
                    ) for library_id in record['library_ids']
                ])
                
                result.update({
                    "status": "pending",
                    "libraries_count": len(record['library_ids'])
                })
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing {instrument_id}: {str(e)}")
                result.update({
                    "status": "error",
                    "error": str(e)
                })
                self.stats["error_count"] += 1
                results.append(result)
        
        # Bulk create all associations in one transaction
        try:
            with transaction.atomic():
                created = LibraryAssociation.objects.bulk_create(
                    associations_to_create,
                    batch_size=BATCH_SIZE  # Keep batch size for database efficiency
                )
                
                self.stats["total_associations_created"] += len(created)
                self.stats["success_count"] += sum(
                    1 for r in results if r["status"] == "pending"
                )
                
                # Update results status
                for result in results:
                    if result["status"] == "pending":
                        result["status"] = "success"
                
        except Exception as e:
            logger.error(f"Bulk creation error in batch {batch_index}: {str(e)}")
            for result in results:
                if result["status"] == "pending":
                    result["status"] = "error"
                    result["error"] = "Bulk creation failed"
                    self.stats["error_count"] += 1
        
        self.stats["processed_count"] += len(records)
        return results

    def process_file(self, data: List[Dict]) -> List[Dict]:
        """Process all records in the file"""
        logger.info(f"Starting to process {len(data)} records")
        
        # Process all records in one batch since file is small
        return self.process_batch(data, 0)

def handler(event, context) -> Dict:
    """
    Lambda handler for processing library linking file
    
    Expected event structure:
    {
        "key": "instrument_library_linkings_1.json"
    }
    """
    start_time = time.time()
    processor = LibraryLinkingProcessor()
    
    assert os.environ['LIBRARY_LINKING_DATA_BUCKET_NAME'], "LIBRARY_LINKING_DATA_BUCKET_NAME is not set"
    
    try:
        # Read data from S3
        response = processor.s3_client.get_object(
            Bucket=os.environ['LIBRARY_LINKING_DATA_BUCKET_NAME'],
            Key=event['key']
        )
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Process the file
        results = processor.process_file(data)
        
        # Prepare summary
        execution_time = time.time() - start_time
        summary = {
            "file_processed": event['key'],
            "total_records": len(data),
            **processor.stats,
            "total_associations": processor.stats["total_associations_created"],
            "execution_time": execution_time,
            "completed": processor.stats["processed_count"] == len(data),
            "results": results
        }
        
        logger.info(f"Processing summary: {summary}")
        
        
        
    except Exception as e:
        logger.error(f"Fatal error processing file {event['key']}: {str(e)}")
        raise
