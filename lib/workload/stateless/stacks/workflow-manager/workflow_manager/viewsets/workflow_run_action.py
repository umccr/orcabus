import json

from datetime import datetime, timezone
from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer

from workflow_manager.aws_event_bridge.event import emit_wrsc_api_event
from workflow_manager.errors import RerunDuplicationError
from workflow_manager.models.utils import create_portal_run_id
from workflow_manager.serializers.library import LibrarySerializer
from workflow_manager.serializers.payload import PayloadSerializer
from workflow_manager.serializers.workflow_run_action import AllowedRerunWorkflow, RERUN_INPUT_SERIALIZERS, \
    AllowedRerunWorkflowSerializer
from workflow_manager.models import (
    WorkflowRun,
    State,
)


class WorkflowRunActionViewSet(ViewSet):
    lookup_value_regex = "[^/]+"  # to allow orcabus id prefix
    queryset = WorkflowRun.objects.prefetch_related('states').all()

    @extend_schema(responses=AllowedRerunWorkflowSerializer, description="Allowed rerun workflows")
    @action(detail=True, methods=['get'], url_name='validate_rerun_workflows', url_path='validate_rerun_workflows')
    def validate_rerun_workflows(self, request, *args, **kwargs):
        wfl_run = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        is_valid = wfl_run.workflow.workflow_name in AllowedRerunWorkflow

        # Get allowed dataset choice for the workflow
        wfl_name = wfl_run.workflow.workflow_name
        allowed_dataset_choice = []
        if wfl_name == AllowedRerunWorkflow.RNASUM.value:
            allowed_dataset_choice = RERUN_INPUT_SERIALIZERS[wfl_name].allowed_dataset_choice

        response = {
            'is_valid': is_valid,
            'allowed_dataset_choice': allowed_dataset_choice,
            'valid_workflows': AllowedRerunWorkflow,
        }
        return Response(response, status=status.HTTP_200_OK)

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name='WorkflowRunRerun',
            serializers=list(RERUN_INPUT_SERIALIZERS.values()),
            resource_type_field_name=None
        ),
        responses=OpenApiTypes.OBJECT,
        description="Trigger a workflow run rerun by emitting an event to EventBridge with an overridden workflow "
                    "input payload. Current supported workflow: 'rnasum'"
    )
    @action(
        detail=True,
        methods=['post'],
        url_name='rerun',
        url_path='rerun'
    )
    def rerun(self, request, *args, **kwargs):
        """
        rerun from existing workflow run
        """
        pk = self.kwargs.get('pk')
        wfl_run = get_object_or_404(self.queryset, pk=pk)

        # Only approved workflow_name is allowed
        if wfl_run.workflow.workflow_name not in AllowedRerunWorkflow:
            return Response(f"This workflow type is not allowed: {wfl_run.workflow.workflow_name}",
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = RERUN_INPUT_SERIALIZERS[wfl_run.workflow.workflow_name](data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            detail = construct_rerun_eb_detail(wfl_run, serializer.data)
        except RerunDuplicationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        emit_wrsc_api_event(detail)

        return Response(detail, status=status.HTTP_200_OK)


def construct_rerun_eb_detail(wfl_run: WorkflowRun, input_body: dict) -> dict:
    """
    Construct event bridge detail for rerun based on the existing workflow run and request body
    """
    new_portal_run_id = create_portal_run_id()
    wfl_name = wfl_run.workflow.workflow_name

    # Each rerun workflow type must implement its own rerun duplication logic and raise `RerunDuplicationError`
    # if it is considered a duplication, unless `allow_duplication` is set to True in the input body.
    new_payload: dict
    if wfl_name == AllowedRerunWorkflow.RNASUM.value:
        new_payload = construct_rnasum_rerun_payload(wfl_run, input_body)
    else:
        raise ValueError(f"Rerun is not allowed for this workflow: {wfl_name}")

    # Replace old portal_run_id with new_portal_run_id in any part of the string
    new_eb_detail = json.loads(
        json.dumps({
            "status": 'READY',
            "payload": new_payload,
            "portalRunId": new_portal_run_id,
            "linkedLibraries": LibrarySerializer(wfl_run.libraries.all(), many=True, camel_case_data=True).data,
            "workflowName": wfl_run.workflow.workflow_name,
            "workflowRunName": wfl_run.workflow_run_name,
            "workflowVersion": wfl_run.workflow.workflow_version,
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        }).replace(f"{wfl_run.portal_run_id}", f"{new_portal_run_id}"))

    return new_eb_detail


def construct_rnasum_rerun_payload(wfl_run: WorkflowRun, input_body: dict) -> dict:
    """
    Construct payload for rerun for 'rnasum' workflow based on the request body payload
    """
    allow_rerun_duplication = input_body.get("allow_duplication", False)

    if not allow_rerun_duplication:
        # The duplication check is based on the dataset input at the READY state of the workflow run that has the same
        # linked libraries and Workflow entity. If the dataset has been run in the past, it will raise an error.

        # Find all workflowrun that has the same linked libraries and Workflow entity
        wfl_runs = WorkflowRun.objects.filter(
            libraries__in=wfl_run.libraries.all(),
            workflow=wfl_run.workflow
        )

        past_dataset = set()
        for run in wfl_runs:
            # Get the payload where the state is 'READY'
            ready_state: State = run.states.get(status='READY')
            ready_data_payload = PayloadSerializer(ready_state.payload).data
            past_dataset.add(ready_data_payload.get('data', {}).get("inputs", {}).get("dataset", ''))

        if input_body["dataset"] in past_dataset:
            raise RerunDuplicationError(f"Dataset '{input_body['dataset']}' has been run in the past. "
                                        f"Set 'allow_duplication' manually to True to proceed.")

    # Get the payload where the state is 'READY'
    ready_state: State = wfl_run.states.get(status='READY')
    ready_data_payload = PayloadSerializer(ready_state.payload).data

    new_data_payload = {
        'version': ready_data_payload['version'],
        'data': ready_data_payload['data']
    }

    # Override payload based on given input
    new_data_payload['data']["inputs"]["dataset"] = input_body["dataset"]

    return new_data_payload
