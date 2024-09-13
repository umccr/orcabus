from drf_spectacular.utils import extend_schema
from rest_framework import filters

from app.models import Project
from app.serializers.project import ProjectSerializer
from app.pagination import StandardResultsSetPagination

from rest_framework.viewsets import ReadOnlyModelViewSet


class ProjectViewSet(ReadOnlyModelViewSet):
    lookup_value_regex = "[^/]+"
    serializer_class = ProjectSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    search_fields = Project.get_base_fields()
    queryset = Project.objects.none()

    @extend_schema(parameters=[
        ProjectSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Project.objects.get_by_keyword(**self.request.query_params)
