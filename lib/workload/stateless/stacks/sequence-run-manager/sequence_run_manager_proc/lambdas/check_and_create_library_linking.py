import os
import logging
import django
from typing import Dict, List
import time
from datetime import datetime

from django.db import transaction
from sequence_run_manager.models.sequence import Sequence, LibraryAssociation
from sequence_run_manager_proc.services.bssh_srv import BSSHService

# Configure logging for AWS Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
BATCH_SIZE = 10  # Process sequences in smaller batches
MAX_EXECUTION_TIME = 840  # 14 minutes (Lambda max is 15 minutes)
ASSOCIATION_STATUS = "ACTIVE"

class LibraryLinkingProcessor:
    def __init__(self):
        self.bssh_service = BSSHService()
        self.start_time = time.time()
        self.processed_count = 0
        self.error_count = 0
        self.success_count = 0
        
    def should_continue_processing(self) -> bool:
        """Check if we should continue processing based on time constraints"""
        return (time.time() - self.start_time) < MAX_EXECUTION_TIME
    
    def process_sequence(self, sequence: Sequence) -> Dict:
        """Process a single sequence and return results"""
        try:
            with transaction.atomic():
                # Skip if already has associations
                if LibraryAssociation.objects.filter(sequence=sequence).exists():
                    return {
                        "status": "skipped",
                        "reason": "existing_associations",
                        "sequence_id": sequence.instrument_run_id
                    }

                # Skip if no API URL
                if not sequence.api_url:
                    return {
                        "status": "skipped",
                        "reason": "no_api_url",
                        "sequence_id": sequence.instrument_run_id
                    }

                # Get run details and create associations
                run_details = self.bssh_service.get_run_details(sequence.api_url)
                libraries = self.bssh_service.get_libraries_from_run_details(run_details)
                
                if not libraries:
                    return {
                        "status": "skipped",
                        "reason": "no_libraries",
                        "sequence_id": sequence.instrument_run_id
                    }

                # Create associations
                created_associations = []
                for library_id in libraries:
                    assoc = LibraryAssociation.objects.create(
                        library_id=library_id,
                        sequence=sequence,
                        status=ASSOCIATION_STATUS
                    )
                    created_associations.append(assoc.library_id)

                return {
                    "status": "success",
                    "sequence_id": sequence.instrument_run_id,
                    "libraries_linked": created_associations
                }

        except Exception as e:
            logger.error(f"Error processing sequence {sequence.instrument_run_id}: {str(e)}")
            return {
                "status": "error",
                "sequence_id": sequence.instrument_run_id,
                "error": str(e)
            }

    def process_batch(self, sequences: List[Sequence]) -> List[Dict]:
        """Process a batch of sequences"""
        results = []
        for sequence in sequences:
            if not self.should_continue_processing():
                logger.warning("Approaching Lambda timeout, stopping batch processing")
                break
                
            result = self.process_sequence(sequence)
            results.append(result)
            
            # Update counters
            self.processed_count += 1
            if result["status"] == "success":
                self.success_count += 1
            elif result["status"] == "error":
                self.error_count += 1
                
        return results

def handler(event, context) -> Dict:
    """
    Lambda handler function
    
    Expected event structure:
    {
        "start_date": "2024-01-01",  # Optional: Process sequences after this date
        "end_date": "2024-03-20",    # Optional: Process sequences before this date
        "batch_size": 10             # Optional: Override default batch size
    }
    """
    try:
        # Initialize processor
        processor = LibraryLinkingProcessor()
        
        # Get sequences query
        sequences_query = Sequence.objects.all()
        
        # Apply date filters if provided
        if event.get('start_date'):
            start_date = datetime.strptime(event['start_date'], '%Y-%m-%d')
            sequences_query = sequences_query.filter(created_at__gte=start_date)
        if event.get('end_date'):
            end_date = datetime.strptime(event['end_date'], '%Y-%m-%d')
            sequences_query = sequences_query.filter(created_at__lte=end_date)
            
        # Get batch size
        batch_size = event.get('batch_size', BATCH_SIZE)
        
        # Process in batches
        all_results = []
        for i in range(0, sequences_query.count(), batch_size):
            if not processor.should_continue_processing():
                logger.warning("Approaching Lambda timeout, stopping processing")
                break
                
            batch = sequences_query[i:i + batch_size]
            batch_results = processor.process_batch(batch)
            all_results.extend(batch_results)

        # Prepare summary
        summary = {
            "total_processed": processor.processed_count,
            "successful": processor.success_count,
            "errors": processor.error_count,
            "execution_time": time.time() - processor.start_time,
            "completed": processor.should_continue_processing(),
            "results": all_results
        }

        logger.info(f"Processing summary: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Fatal error in lambda execution: {str(e)}")
        raise
