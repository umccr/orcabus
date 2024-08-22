from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from workflow_manager.models.library import Library
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import LibraryModelSerializer


class LibraryViewSet(ReadOnlyModelViewSet):
    serializer_class = LibraryModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    ordering = ['-orcabus_id']
    search_fields = Library.get_base_fields()

    def get_queryset(self):
        qs = Library.objects.filter(workflowrun=self.kwargs["workflowrun_id"])
        qs = Library.objects.get_model_fields_query(qs, **self.request.query_params)
        return qs
