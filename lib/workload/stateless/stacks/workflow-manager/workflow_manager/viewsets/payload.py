from drf_spectacular.utils import extend_schema

from workflow_manager.models.payload import Payload
from workflow_manager.serializers.payload import PayloadSerializer
from workflow_manager.viewsets.base import BaseViewSet


class PayloadViewSet(BaseViewSet):
    serializer_class = PayloadSerializer
    search_fields = Payload.get_base_fields()
    orcabus_id_prefix = Payload.orcabus_id_prefix

    def get_queryset(self):
        query_params = self.get_query_params()
        return Payload.objects.get_by_keyword(self.queryset, **query_params)
