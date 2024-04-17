from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.pagination import StandardResultsSetPagination
from sequence_run_manager.serializers import SequenceSerializer


class SequenceViewSet(ReadOnlyModelViewSet):
    serializer_class = SequenceSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-id"]
    search_fields = Sequence.get_base_fields()

    def get_queryset(self):
        return Sequence.objects.get_by_keyword(**self.request.query_params)
