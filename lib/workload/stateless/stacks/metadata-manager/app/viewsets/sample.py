from drf_spectacular.utils import extend_schema
from rest_framework import filters

from app.models import Sample
from app.serializers.sample import SampleSerializer
from app.pagination import StandardResultsSetPagination

from rest_framework.viewsets import ReadOnlyModelViewSet


class SampleViewSet(ReadOnlyModelViewSet):
    lookup_value_regex = "[^/]+"
    serializer_class = SampleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    search_fields = Sample.get_base_fields()
    queryset = Sample.objects.none()

    @extend_schema(parameters=[
        SampleSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Sample.objects.get_by_keyword(**self.request.query_params)
