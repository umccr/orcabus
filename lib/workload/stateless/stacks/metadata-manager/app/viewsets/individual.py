from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from app.models import Individual
from app.serializers.individual import IndividualDetailSerializer, IndividualHistorySerializer, IndividualSerializer

from .base import BaseViewSet


class IndividualViewSet(BaseViewSet):
    serializer_class = IndividualSerializer
    search_fields = Individual.get_base_fields()
    queryset = Individual.objects.all()
    orcabus_id_prefix = Individual.orcabus_id_prefix

    @extend_schema(responses=IndividualDetailSerializer(many=False))
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = IndividualDetailSerializer
        self.queryset = Individual.objects.prefetch_related('subject_set').all()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[IndividualDetailSerializer],
        responses=IndividualDetailSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.serializer_class = IndividualDetailSerializer
        self.queryset = Individual.objects.prefetch_related('subject_set').all()
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return Individual.objects.get_by_keyword(self.queryset, **query_params)

    @extend_schema(responses=IndividualHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(IndividualHistorySerializer)

