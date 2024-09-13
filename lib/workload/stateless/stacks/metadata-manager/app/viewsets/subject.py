from drf_spectacular.utils import extend_schema
from rest_framework import filters

from app.models import Subject
from app.serializers.subject import SubjectSerializer
from app.pagination import StandardResultsSetPagination

from rest_framework.viewsets import ReadOnlyModelViewSet


class SubjectViewSet(ReadOnlyModelViewSet):
    lookup_value_regex = "[^/]+"
    serializer_class = SubjectSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    search_fields = Subject.get_base_fields()
    queryset = Subject.objects.none()

    @extend_schema(parameters=[
        SubjectSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Subject.objects.get_by_keyword(**self.request.query_params)


