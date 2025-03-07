import django

django.setup()

# --- keep ^^^ at top of the module
from case_manager.models.case_run import CaseRun
import case_manager_proc.domain.executionservice.caserunstatechange as srv
import case_manager_proc.domain.casemanager.caserunstatechange as case
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    """event will be a casemanager.CaseRunStateChange event"""
    logger.info(f"Processing {event}, {context}")
    
    input_event: case.AWSEvent = case.Marshaller.unmarshall(event, case.AWSEvent)
    input_wrsc: case.CaseRunStateChange = input_event.detail
    
    ## Trigger signal is the announcement from the casemanager that the bclconvert case run has succeeded
    ## business logic as follows:
	# receive a casemanager.CaseRunStateChange event for "bclconvert succeeded": caseName = "BclConvert", caseVersion = "4.2.13"
	# check:
    #    needs to be a BclConvert event
    #    needs to be a supported version (whatever we know how to map)
    #    needs to be a succeeded status
    # parse the succeeded payload
    # map from bclconvert event to fastq copy event payload
    # create fastq copy payload
    # create service CaseRunStateChange for fastqcopy with ready payload
    # send a <glue service>.CaseRunStateChange event for "fastq copy ready": caseName = "FastqCopy", caseVersion = "1.0.0" (simulate PolicyManager schedulling FASTQ copy)
    ## result is that the case manager will ingest the <glue service> event, register the new state (ready) and emit a casemanager event announcing the same

def check_input_event():
    pass

def map_input_to_output():
    # read input payload  (bclconvertmanager success)
    # generate output payload  (fastq-copy ready)
    pass

def emit_output_event():
    pass