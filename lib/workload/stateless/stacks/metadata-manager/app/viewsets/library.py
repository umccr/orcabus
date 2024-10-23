from drf_spectacular.utils import extend_schema
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

        coverage__lte = query_params.get("coverage__lte", None)
        if coverage__lte:
            query_params.pop("coverage__lte")
            qs = qs.filter(coverage__lte=coverage__lte)

        coverage__gte = query_params.get("coverage__gte", None)
        if coverage__gte:
            query_params.pop("coverage__gte")
            qs = qs.filter(coverage__gte=coverage__gte)

        # Continue filtering by the keys inside the library model
        return Library.objects.get_by_keyword(qs, **query_params)

    @extend_schema(parameters=[
        LibrarySerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=LibraryHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(LibraryHistorySerializer)
