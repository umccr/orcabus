from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from app.models import Project
from app.serializers.project import ProjectDetailSerializer, ProjectSerializer, ProjectHistorySerializer

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

    @extend_schema(responses=ProjectHistorySerializer(many=True))
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(ProjectHistorySerializer)
