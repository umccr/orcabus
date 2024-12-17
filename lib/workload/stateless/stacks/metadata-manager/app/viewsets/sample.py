from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action

from app.models import Sample
from app.serializers.sample import SampleSerializer, SampleDetailSerializer, SampleHistorySerializer

from .base import BaseViewSet


class SampleViewSet(BaseViewSet):
    serializer_class = SampleSerializer
    search_fields = Sample.get_base_fields()
    queryset = Sample.objects.all()

    def get_queryset(self):
        qs = self.queryset
        query_params = self.request.query_params.copy()

        is_library_none = query_params.getlist("is_library_none", None)
        if is_library_none:
            query_params.pop("is_library_none")
            qs = qs.filter(library=None)

        return Sample.objects.get_by_keyword(qs, **query_params)

    @extend_schema(responses=SampleDetailSerializer(many=False))
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = SampleDetailSerializer
        self.queryset = Sample.objects.prefetch_related('library_set').all()
        return super().retrieve(request, *args, **kwargs)


    @extend_schema(
        parameters=[
            SampleSerializer,
            OpenApiParameter(name='is_library_none',
                             description="Filter where it is not linked to a library.",
                             required=False,
                             type=bool),
        ],
        responses=SampleDetailSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.queryset = Sample.objects.prefetch_related('library_set').all()
        self.serializer_class = SampleDetailSerializer
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=SampleHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(SampleHistorySerializer)
