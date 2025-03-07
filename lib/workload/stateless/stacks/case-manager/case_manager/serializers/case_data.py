from case_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from case_manager.models import CaseData


class PayloadBaseSerializer(SerializersBase):
    pass

class CaseDataListParamSerializer(OptionalFieldsMixin, PayloadBaseSerializer):
    class Meta:
        model = CaseData
        fields = "__all__"

class CaseDataSerializer(PayloadBaseSerializer):
    class Meta:
        model = CaseData
        fields = "__all__"
