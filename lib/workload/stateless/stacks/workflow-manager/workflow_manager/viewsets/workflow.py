from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from workflow_manager.models.workflow import Workflow
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import WorkflowModelSerializer


class WorkflowViewSet(ModelViewSet):
    serializer_class = WorkflowModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    search_fields = ordering_fields
    ordering = ['-id']
    queryset = Workflow.objects.all()
