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
    ordering = ['-id']
    search_fields = Library.get_base_fields()

    def get_queryset(self):
        return Library.objects.get_by_keyword(**self.request.query_params)
