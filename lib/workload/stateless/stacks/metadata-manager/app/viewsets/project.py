from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from app.models import Project
from app.serializers.project import ProjectDetailSerializer, ProjectSerializer, ProjectHistorySerializer

from .base import BaseViewSet


class ProjectViewSet(BaseViewSet):
    serializer_class = ProjectSerializer
    search_fields = Project.get_base_fields()
    queryset = Project.objects.all()
    orcabus_id_prefix = Project.orcabus_id_prefix

    @extend_schema(responses=ProjectDetailSerializer(many=False))
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = ProjectDetailSerializer
        self.queryset = Project.objects.prefetch_related("contact_set").all()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            ProjectSerializer
        ],
        responses=ProjectDetailSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.serializer_class = ProjectDetailSerializer
        self.queryset = Project.objects.prefetch_related("contact_set").all()
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return Project.objects.get_by_keyword(self.queryset, **query_params)

    @extend_schema(responses=ProjectHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(ProjectHistorySerializer)
