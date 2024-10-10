from drf_spectacular.utils import extend_schema

from app.models import Project
from app.serializers.project import ProjectDetailSerializer, ProjectSerializer

from .base import BaseViewSet


class ProjectViewSet(BaseViewSet):
    serializer_class = ProjectDetailSerializer
    search_fields = Project.get_base_fields()
    queryset = Project.objects.prefetch_related("contact_set").prefetch_related("library_set").all()
    orcabus_id_prefix = Project.orcabus_id_prefix

    @extend_schema(parameters=[
        ProjectSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return Project.objects.get_by_keyword(self.queryset, **query_params)
