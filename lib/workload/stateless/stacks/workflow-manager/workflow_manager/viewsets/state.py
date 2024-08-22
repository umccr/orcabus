from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from workflow_manager.models import State
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import StateModelSerializer


class StateViewSet(ReadOnlyModelViewSet):
    serializer_class = StateModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    ordering = ['-id']
    search_fields = State.get_base_fields()

    def get_queryset(self):
        qs = State.objects.filter(workflow_run=self.kwargs["workflowrun_id"])
        qs = State.objects.get_model_fields_query(qs, **self.request.query_params)
        return qs


