from drf_spectacular.utils import extend_schema

from workflow_manager.models.workflow import Workflow
from workflow_manager.serializers.workflow import WorkflowSerializer, WorkflowListParamSerializer
from workflow_manager.viewsets.base import BaseViewSet


class WorkflowViewSet(BaseViewSet):
    serializer_class = WorkflowSerializer
    search_fields = Workflow.get_base_fields()

    @extend_schema(parameters=[
        WorkflowListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.request.query_params.copy()
        return Workflow.objects.get_by_keyword(self.queryset, **query_params)
