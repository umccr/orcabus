from drf_spectacular.utils import extend_schema

from workflow_manager.models.workflow import Workflow
from workflow_manager.serializers.workflow import WorkflowSerializer
from workflow_manager.viewsets.base import BaseViewSet


class WorkflowViewSet(BaseViewSet):
    serializer_class = WorkflowSerializer
    search_fields = Workflow.get_base_fields()
    orcabus_id_prefix = Workflow.orcabus_id_prefix

    @extend_schema(parameters=[
        WorkflowSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return Workflow.objects.get_by_keyword(self.queryset, **query_params)
