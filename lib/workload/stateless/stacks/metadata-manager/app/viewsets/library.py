from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action

from app.models import Library
from app.serializers.library import LibrarySerializer, LibraryDetailSerializer, LibraryHistorySerializer

from .base import BaseViewSet


class LibraryViewSet(BaseViewSet):
    serializer_class = LibraryDetailSerializer
    search_fields = Library.get_base_fields()
    queryset = Library.objects.select_related('sample').select_related('subject').prefetch_related('project_set').all()
    orcabus_id_prefix = Library.orcabus_id_prefix

    def get_queryset(self):
        qs = self.queryset
        query_params = self.get_query_params()

        coverage__lte = query_params.get("coverage[lte]", None)
        if coverage__lte:
            query_params.pop("coverage[lte]")
            qs = qs.filter(coverage__lte=coverage__lte)

        coverage__gte = query_params.get("coverage[gte]", None)
        if coverage__gte:
            query_params.pop("coverage[gte]")
            qs = qs.filter(coverage__gte=coverage__gte)

        project_id = query_params.get("project_id", None)
        if project_id:
            query_params.pop("project_id")
            qs = qs.filter(project_set__project_id=project_id)

        # Continue filtering by the keys inside the library model
        return Library.objects.get_by_keyword(qs, **query_params)

    @extend_schema(parameters=[
        LibrarySerializer,
        OpenApiParameter(name='coverage[lte]',
                         description="Filter based on 'coverage' that is less than or equal to the given value.",
                         required=False,
                         type=float),
        OpenApiParameter(name='coverage[gte]',
                         description="Filter based on 'coverage' that is greater than or equal to the given value.",
                         required=False,
                         type=float),
        OpenApiParameter(name='project_id',
                         description="Filter where the associated the project has the given 'project_id'.",
                         required=False,
                         type=float),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=LibraryHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(LibraryHistorySerializer)
