from drf_spectacular.utils import extend_schema

from workflow_manager.models import State
from workflow_manager.serializers.state import StateSerializer
from workflow_manager.viewsets.base import BaseViewSet


class StateViewSet(BaseViewSet):
    serializer_class = StateSerializer
    search_fields = State.get_base_fields()
    orcabus_id_prefix = State.orcabus_id_prefix

    @extend_schema(parameters=[
        StateSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        # qs = State.objects.filter(workflow_run=self.kwargs["workflowrun_id"])
        return State.objects.get_by_keyword(qs, **query_params)
