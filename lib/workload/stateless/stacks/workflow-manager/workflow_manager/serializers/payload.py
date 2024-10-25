from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from workflow_manager.models import Payload


class PayloadBaseSerializer(SerializersBase):
    prefix = Payload.orcabus_id_prefix

class PayloadListParamSerializer(OptionalFieldsMixin, PayloadBaseSerializer):
    class Meta:
        model = Payload
        fields = "__all__"

class PayloadSerializer(PayloadBaseSerializer):
    class Meta:
        model = Payload
        fields = "__all__"
