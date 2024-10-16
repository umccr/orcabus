from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action

from app.models import Subject, Library
from app.serializers.subject import SubjectSerializer, SubjectDetailSerializer, SubjectHistorySerializer
from .base import BaseViewSet


class SubjectViewSet(BaseViewSet):
    serializer_class = SubjectDetailSerializer
    search_fields = Subject.get_base_fields()
    queryset = Subject.objects.prefetch_related('individual_set').prefetch_related('library_set').all()
    orcabus_id_prefix = Subject.orcabus_id_prefix

    def get_queryset(self):

        qs = self.queryset
        query_params = self.get_query_params()

        library_id = query_params.get("library_id", None)
        if library_id:
            query_params.pop("library_id")
            qs = qs.filter(library__library_id=library_id)

        library_orcabus_id = query_params.get("library_orcabus_id", None)
        if library_orcabus_id:
            query_params.pop("library_orcabus_id")

            # Remove '.lib' prefix if present
            if library_orcabus_id.startswith(Library.orcabus_id_prefix):
                library_orcabus_id = library_orcabus_id[len(self.orcabus_id_prefix):]

            qs = qs.filter(library__orcabus_id=library_orcabus_id)

        return Subject.objects.get_by_keyword(qs, **query_params)

    @extend_schema(parameters=[
        SubjectSerializer,
        OpenApiParameter(name='library_id',
                         description="Filter based on 'library_id' of the library associated with the subject.",
                         required=False,
                         type=str),
        OpenApiParameter(name='library_orcabus_id',
                         description="Filter based on 'orcabus_id' of the library associated with the subject.",
                         required=False,
                         type=str),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=SubjectHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(SubjectHistorySerializer)
