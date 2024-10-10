from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import Payload


class PayloadBaseSerializer(SerializersBase):
    prefix = Payload.orcabus_id_prefix


class PayloadSerializer(PayloadBaseSerializer):
    class Meta:
        model = Payload
        fields = "__all__"
