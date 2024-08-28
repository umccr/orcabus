from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from workflow_manager.models.workflow_run import WorkflowRun
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import WorkflowRunModelSerializer


class WorkflowRunViewSet(ReadOnlyModelViewSet):
    serializer_class = WorkflowRunModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    ordering = ['-id']
    search_fields = WorkflowRun.get_base_fields()

    def get_queryset(self):
        return WorkflowRun.objects.get_by_keyword(**self.request.query_params)
