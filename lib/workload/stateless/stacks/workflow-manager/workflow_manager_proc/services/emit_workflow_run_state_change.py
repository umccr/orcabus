import os
import boto3
import json
import workflow_manager_proc.domain.workflowmanager.workflowrunstatechange as wfm
from workflow_manager_proc.domain.workflowmanager.workflowrunstatechange import WorkflowRunStateChange

client = boto3.client('events')
source = "orcabus.workflowmanager"
event_bus_name = os.environ["EVENT_BUS_NAME"]

def handler(event, context):
    """
    event has to be JSON conform to workflowmanager.WorkflowRunStateChange
    """
    print(f"Processing {event}, {context}")

    response = client.put_events(
		Entries=[
			{
				'Source': source,
				'DetailType': WorkflowRunStateChange.__name__,
				'Detail': json.dumps(wfm.Marshaller.marshall(event)),
				'EventBusName': event_bus_name,
			},
		],
	)

    print(f"Sent a WRSC event to event bus {event_bus_name}:")
    print(event)
    print(f"{__name__} done.")
    return response
