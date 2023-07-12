from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from library_manager.models.library import Library
from library_manager.pagination import StandardResultsSetPagination
from library_manager.serializers import LibraryModelSerializer


class LibraryViewSet(ModelViewSet):
    serializer_class = LibraryModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    search_fields = ordering_fields
    ordering = ["-id"]
    queryset = Library.objects.all()
