from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action

from app.models import Subject, Library
from app.serializers.subject import SubjectSerializer, SubjectDetailSerializer, SubjectHistorySerializer
from .base import BaseViewSet


class SubjectViewSet(BaseViewSet):
    serializer_class = SubjectSerializer
    search_fields = [*Subject.get_base_fields(), 'library__library_id','individual_set__individual_id']
    queryset = Subject.objects.all()

    def get_queryset(self):

        qs = self.queryset
        query_params = self.request.query_params.copy()

        library_id = query_params.get("library_id", None)
        if library_id:
            query_params.pop("library_id")
            qs = qs.filter(library__library_id=library_id)

        is_library_none = query_params.getlist("is_library_none", None)
        if is_library_none:
            query_params.pop("is_library_none")
            qs = qs.filter(library=None)

        # This is a temporary solution to quickly retrieve libraries based on the individual_id (the SBJXXX ID) as it is commonly used.
        # This approach may be improved in the future.
        individual_id_list = query_params.getlist("individual_id", None)
        if individual_id_list:
            query_params.pop("individual_id")
            qs = qs.filter(individual_set__individual_id__in=individual_id_list)

        return Subject.objects.get_by_keyword(qs, **query_params)


    @extend_schema(responses=SubjectDetailSerializer(many=False))
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = SubjectDetailSerializer
        self.queryset = Subject.objects.prefetch_related('individual_set').prefetch_related('library_set').all()
        return super().retrieve(request, *args, **kwargs)



    @extend_schema(
        parameters=[
            SubjectSerializer,
            OpenApiParameter(name='library_id',
                             description="Filter based on 'library_id' of the library associated with the subject.",
                             required=False,
                             type=str),
            OpenApiParameter(name='library_orcabus_id',
                             description="Filter based on 'orcabus_id' of the library associated with the subject.",
                             required=False,
                             type=str),
            OpenApiParameter(name='is_library_none',
                             description="Filter where it is not linked to a library.",
                             required=False,
                             type=bool),
            OpenApiParameter(name='individual_id',
                             description="Filter based on 'individual_id' linked to this library (E.g. SBJXXXXX).",
                             required=False,
                             type=str),
        ],
        responses=SubjectDetailSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.serializer_class = SubjectDetailSerializer
        self.queryset = Subject.objects.prefetch_related('individual_set').prefetch_related('library_set').all()
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=SubjectHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(SubjectHistorySerializer)
