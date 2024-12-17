from drf_spectacular.utils import extend_schema

from workflow_manager.models.payload import Payload
from workflow_manager.serializers.payload import PayloadSerializer, PayloadListParamSerializer
from workflow_manager.viewsets.base import BaseViewSet


class PayloadViewSet(BaseViewSet):
    serializer_class = PayloadSerializer
    search_fields = Payload.get_base_fields()

    @extend_schema(parameters=[
        PayloadListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.request.query_params.copy()
        return Payload.objects.get_by_keyword(self.queryset, **query_params)
