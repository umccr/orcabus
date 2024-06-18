from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from workflow_manager.models.payload import Payload
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import PayloadModelSerializer


class PayloadViewSet(ReadOnlyModelViewSet):
    serializer_class = PayloadModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    search_fields = ordering_fields
    ordering = ['-id']
    queryset = Payload.objects.all()
