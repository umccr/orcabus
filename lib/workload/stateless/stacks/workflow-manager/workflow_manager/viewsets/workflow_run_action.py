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
from workflow_manager.models.utils import create_portal_run_id
from workflow_manager.serializers.library import LibrarySerializer
from workflow_manager.serializers.payload import PayloadSerializer
from workflow_manager.serializers.workflow_run_action import AllowedRerunWorkflow, RERUN_INPUT_SERIALIZERS
from workflow_manager.models import (
    WorkflowRun,
    State,
)


class WorkflowRunActionViewSet(ViewSet):
    lookup_value_regex = "[^/]+"  # to allow orcabus id prefix
    queryset = WorkflowRun.objects.prefetch_related('states').all()
    orcabus_id_prefix = WorkflowRun.orcabus_id_prefix

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name='WorkflowRunRerun',
            serializers=list(RERUN_INPUT_SERIALIZERS.values()),
            resource_type_field_name=None
        ),
        responses=OpenApiTypes.OBJECT,
        description="Trigger a workflow run rerun by emitting an event to EventBridge with an overridden workflow "
                    "input payload. (Current supported workflow: 'rnasum')"
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
        if pk and pk.startswith(self.orcabus_id_prefix):
            pk = pk[len(self.orcabus_id_prefix):]
        wfl_run = get_object_or_404(self.queryset, pk=pk)

        # Only approved workflow_name is allowed
        if wfl_run.workflow.workflow_name not in AllowedRerunWorkflow:
            return Response(f"This workflow type is not allowed: {wfl_run.workflow.workflow_name}",
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = RERUN_INPUT_SERIALIZERS[wfl_run.workflow.workflow_name](data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        detail = construct_rerun_eb_detail(wfl_run, serializer.data)
        emit_wrsc_api_event(detail)

        return Response(detail, status=status.HTTP_200_OK)


def construct_rerun_eb_detail(wfl_run: WorkflowRun, input_body: dict) -> dict:
    """
    Construct event bridge detail for rerun based on the existing workflow run and request body
    """
    new_portal_run_id = create_portal_run_id()
    wfl_name = wfl_run.workflow.workflow_name

    new_payload: dict
    if wfl_name == AllowedRerunWorkflow.RNASUM.value:
        new_payload = construct_rnasum_rerun_payload(wfl_run, new_portal_run_id, input_body)
    else:
        raise ValueError(f"Rerun is not allowed for this workflow: {wfl_name}")

    return {
        "status": 'READY',
        "payload": new_payload,
        "portalRunId": new_portal_run_id,
        "linkedLibraries": LibrarySerializer(wfl_run.libraries.all(), many=True).data,
        "workflowName": wfl_run.workflow.workflow_name,
        "workflowRunName": wfl_run.workflow_run_name,
        "workflowVersion": wfl_run.workflow.workflow_version,
        "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }


def construct_rnasum_rerun_payload(wfl_run: WorkflowRun, new_portal_run_id: str, input_body: dict) -> dict:
    """
    Construct payload for rerun for 'rnasum' workflow based on the request body payload
    """

    # Get the payload where the state is 'READY'
    ready_state: State = wfl_run.states.get(status='READY')
    ready_data_payload = PayloadSerializer(ready_state.payload).data.get("data", None)

    # Start crafting the payload based on the old ones
    new_data_payload = ready_data_payload.copy()

    # Override payload based on given input
    new_data_payload["inputs"]["dataset"] = input_body["dataset"]

    # Replace old portal_run_id with new_portal_run_id in any part of the string
    # In the 'rnasum` payload, the engine parameter URI prefixes contain the portal_run_id
    new_data_payload = json.loads(
        json.dumps(new_data_payload).replace(f"{wfl_run.portal_run_id}", f"{new_portal_run_id}"))

    return new_data_payload
