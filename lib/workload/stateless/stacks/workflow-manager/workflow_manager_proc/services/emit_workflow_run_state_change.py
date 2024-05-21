import os
import boto3
from workflow_manager_proc.domain.workflowmanager.workflowrunstatechange import WorkflowRunStateChange

client = boto3.client('events')
source = "orcabus.workflowmanager"
event_bus_name = os.environ["ORCABUS_EVENT_BUS_NAME"]

def handler(event, context):
    """event has to be JSON conform to workflowmanager.WorkflowRunStateChange
    """
    print(f"Processing {event}, {context}")
    
    response = client.put_events(
		Entries=[
			{
				'Source': source,
				'DetailType': WorkflowRunStateChange.__name__,
				'Detail': event,
				'EventBusName': event_bus_name,
			},
		],
	)

    return response
