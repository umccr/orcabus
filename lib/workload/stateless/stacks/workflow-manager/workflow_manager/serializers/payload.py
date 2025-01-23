from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin, OrcabusIdSerializerMetaMixin
from workflow_manager.models import Payload


class PayloadBaseSerializer(SerializersBase):
    pass


class PayloadListParamSerializer(OptionalFieldsMixin, PayloadBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Payload
        fields = "__all__"


class PayloadSerializer(PayloadBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Payload
        fields = "__all__"
