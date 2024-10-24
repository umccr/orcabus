from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from app.models import Sample
from app.serializers.sample import SampleSerializer, SampleDetailSerializer, SampleHistorySerializer

from .base import BaseViewSet


class SampleViewSet(BaseViewSet):
    serializer_class = SampleDetailSerializer
    search_fields = Sample.get_base_fields()
    queryset = Sample.objects.all()
    orcabus_id_prefix = Sample.orcabus_id_prefix

    @extend_schema(parameters=[
        SampleSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return Sample.objects.get_by_keyword(**query_params)

    @extend_schema(responses=SampleHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(SampleHistorySerializer)
