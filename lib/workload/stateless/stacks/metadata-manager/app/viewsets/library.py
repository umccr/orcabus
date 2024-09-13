from drf_spectacular.utils import extend_schema
from rest_framework import filters

from app.models import Library
from app.serializers.library import LibrarySerializer
from app.pagination import StandardResultsSetPagination

from rest_framework.viewsets import ReadOnlyModelViewSet


class LibraryViewSet(ReadOnlyModelViewSet):
    lookup_value_regex = "[^/]+"
    serializer_class = LibrarySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    search_fields = Library.get_base_fields()
    queryset = Library.objects.none()

    def get_queryset(self):
        qs = Library.objects.all()
        query_params = self.request.query_params.copy()

        coverage__lte = query_params.get("coverage__lte", None)
        if coverage__lte:
            query_params.pop("coverage__lte")
            qs = qs.filter(coverage__lte=coverage__lte)

        coverage__gte = query_params.get("coverage__gte", None)
        if coverage__gte:
            query_params.pop("coverage__gte")
            qs = qs.filter(coverage__gte=coverage__gte)

        # Continue filtering by the keys inside the library model
        return Library.objects.get_model_fields_query(qs, **query_params)

    @extend_schema(parameters=[
        LibrarySerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


