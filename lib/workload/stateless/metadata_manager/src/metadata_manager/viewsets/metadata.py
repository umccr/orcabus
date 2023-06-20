from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from metadata_manager.models.metadata import Metadata
from metadata_manager.pagination import StandardResultsSetPagination
from metadata_manager.serializers import MetadataModelSerializer


class MetadataViewSet(ModelViewSet):
    serializer_class = MetadataModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    search_fields = ordering_fields
    ordering = ["-id"]
    queryset = Metadata.objects.all()
