from drf_spectacular.utils import extend_schema

from app.models import Project
from app.serializers.project import ProjectDetailSerializer, ProjectSerializer

from .base import BaseViewSet


class ProjectViewSet(BaseViewSet):
    serializer_class = ProjectDetailSerializer
    search_fields = Project.get_base_fields()
    queryset = Project.objects.prefetch_related("contact_set").all()

    @extend_schema(parameters=[
        ProjectSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Project.objects.get_by_keyword(self.queryset, **self.request.query_params)
