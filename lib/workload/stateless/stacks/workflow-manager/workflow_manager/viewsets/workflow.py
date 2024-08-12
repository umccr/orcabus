from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from workflow_manager.models.workflow import Workflow
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import WorkflowModelSerializer


class WorkflowViewSet(ReadOnlyModelViewSet):
    serializer_class = WorkflowModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    ordering = ['-id']
    search_fields = Workflow.get_base_fields()

    def get_queryset(self):
        return Workflow.objects.get_by_keyword(**self.request.query_params)
