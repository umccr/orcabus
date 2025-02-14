from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action

from app.models import Library, Subject
from app.serializers.library import LibrarySerializer, LibraryDetailSerializer, LibraryHistorySerializer

from .base import BaseViewSet


class LibraryViewSet(BaseViewSet):
    serializer_class = LibrarySerializer
    detail_serializer_class = LibraryDetailSerializer
    search_fields = Library.get_base_fields()
    queryset = Library.objects.all()


    def get_queryset(self):
        qs = self.queryset
        query_params = self.request.query_params.copy()

        coverage__lte = query_params.get("coverage[lte]", None)
        if coverage__lte:
            query_params.pop("coverage[lte]")
            qs = qs.filter(coverage__lte=coverage__lte)

        coverage__gte = query_params.get("coverage[gte]", None)
        if coverage__gte:
            query_params.pop("coverage[gte]")
            qs = qs.filter(coverage__gte=coverage__gte)

        project_id_list = query_params.getlist("project_id", None)
        if project_id_list:
            query_params.pop("project_id")
            qs = qs.filter(project_set__project_id__in=project_id_list)

        # This is a temporary solution to quickly retrieve libraries based on the individual_id (the SBJXXX ID) as it is commonly used.
        # This approach may be improved in the future.
        individual_id_list = query_params.getlist("individual_id", None)
        if individual_id_list:
            query_params.pop("individual_id")

            # Find the related subject with the individual_id
            f_sbj = Subject.objects.filter(individual_set__individual_id__in=individual_id_list)
            qs = qs.filter(subject__in=f_sbj)

        # Continue filtering by the keys inside the library model
        return Library.objects.get_by_keyword(qs, **query_params)

    @extend_schema(responses=LibraryDetailSerializer(many=False))
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = LibraryDetailSerializer
        self.queryset = Library.objects.select_related('sample').select_related('subject').prefetch_related(
            'project_set').all()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
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
            OpenApiParameter(name='individual_id',
                             description="Filter based on 'individual_id' linked to this library (E.g. SBJXXXXX).",
                             required=False,
                             type=str),
        ],
        responses=LibraryDetailSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.serializer_class = LibraryDetailSerializer
        self.queryset = Library.objects.select_related('sample').select_related('subject').prefetch_related(
            'project_set').all()
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=LibraryHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(LibraryHistorySerializer)
