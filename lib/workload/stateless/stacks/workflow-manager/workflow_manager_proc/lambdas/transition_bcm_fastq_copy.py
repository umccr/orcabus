import django

django.setup()

# --- keep ^^^ at top of the module
from workflow_manager.models.workflow_run import WorkflowRun
import workflow_manager_proc.domain.executionservice.workflowrunstatechange as srv
import workflow_manager_proc.domain.workflowmanager.workflowrunstatechange as wfm
from workflow_manager_proc.services import get_workflow_run, create_workflow_run, emit_workflow_run_state_change


def handler(event, context):
    """event will be a workflowmanager.WorkflowRunStateChange event"""
    print(f"Processing {event}, {context}")
    
    input_event: wfm.AWSEvent = wfm.Marshaller.unmarshall(event, wfm.AWSEvent)
    input_wrsc: wfm.WorkflowRunStateChange = input_event.detail
    
    ## Trigger signal is the announcement from the workflowmanager that the bclconvert workflow run has succeeded
    ## business logic as follows:
	# receive a workflowmanager.WorkflowRunStateChange event for "bclconvert succeeded": workflowName = "BclConvert", workflowVersion = "4.2.13"
	# check:
    #    needs to be a BclConvert event
    #    needs to be a supported version (whatever we know how to map)
    #    needs to be a succeeded status
    # parse the succeeded payload
    # map from bclconvert event to fastq copy event payload
    # create fastq copy payload
    # create service WorkflowRunStateChange for fastqcopy with ready payload
    # send a <glue service>.WorkflowRunStateChange event for "fastq copy ready": workflowName = "FastqCopy", workflowVersion = "1.0.0" (simulate PolicyManager schedulling FASTQ copy)
    ## result is that the workflow manager will ingest the <glue service> event, register the new state (ready) and emit a workflowmanager event announcing the same

def check_input_event():
    pass

def map_input_to_output():
    # read input payload  (bclconvertmanager success)
    # generate output payload  (fastq-copy ready)
    pass

def emit_output_event():
    pass