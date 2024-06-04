from django.core.management import BaseCommand
from django.db.models import QuerySet

import json
from datetime import datetime
from workflow_manager.models import WorkflowRun
from workflow_manager_proc.lambdas import handle_service_wrsc_event
from workflow_manager.tests.factories import WorkflowRunFactory, WorkflowFactory,  PayloadFactory


mock_event = {
    "version": "0",
    "id": "1",
    "detail-type": "WorkflowRunStateChange",
    "source": "orcabus.foomanager",
    "account": "843407916570",
    "time": "2024-06-03T10:37:30Z",
    "region": "ap-southeast-2",
    "detail": {
        "workflowName": "test_workflow",
        "workflowVersion": "1.0.0",
        "payload": {
            "version": "2024.05.07",
            "data": {
                "analysisId": "aid1",
                "projectId": "pid1",
                "analysisOutput": "ica://foo/bar"
            }
        },
        "portalRunId": "2024060312345678",
        "workflowRunName": "mock__automated__test_workflow",
        "timestamp": "2024-06-03T10:37:30.558Z",
        "status": "DRAFT"
    }
}

default_payload = {
    "analysisId": "ais1",
    "projectId": "pid1",
    "analysisOutput": "ica://foo/bar"
}


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Generate mock Workflow data into database for local development and testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--status", 
            help="The status to set for the WorkflowRunStateChange event.",
            default='DRAFT'
        )
        parser.add_argument(
            "--portal-run-id", 
            help="The portal_run_id to set for the WorkflowRunStateChange event.",
            default='2024060312345678'
        )
        parser.add_argument(
            "--payload-data", 
            help="The payload data to set for the WorkflowRunStateChange event.",
            default=json.dumps(default_payload)
        )

    def handle(self, *args, **options):
        opt_status = options['status']
        opt_portal_run_id = options['portal_run_id']
        opt_data = options['payload_data']
        try:
            opt_data = json.loads(opt_data)
        except json.decoder.JSONDecodeError as err:
            print("payload data needs to be a valid JSON string!")
            raise err

        event = mock_event
        overwrite_status(event, opt_status)
        overwrite_portal_run_id(event, opt_portal_run_id)
        overwrite_payload_data(event, opt_data)
        overwrite_time(event, datetime.now())
        handle_service_wrsc_event.handler(event, None)


def overwrite_time(event, custom_time: datetime):
    print(f"Overwriting event time with: {custom_time}")
    event['time'] = str(custom_time)
    event['detail']['timestamp'] = str(custom_time)


def overwrite_portal_run_id(event, portal_run_id: str):
    print(f"Overwriting portal_run_id with: {portal_run_id}")
    event['detail']['portalRunId'] = portal_run_id


def overwrite_status(event, status: str):
    print(f"Overwriting status with: {status}")
    event['detail']['status'] = status.upper()


def overwrite_payload_data(event, data: dict):
    print(f"Overwriting payload data with: {data}")
    event['detail']['payload']['data'] = data
