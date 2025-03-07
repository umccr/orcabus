from case_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from case_manager.models import Case


class CaseBaseSerializer(SerializersBase):
    pass

class CaseListParamSerializer(OptionalFieldsMixin, CaseBaseSerializer):
    class Meta:
        model = Case
        fields = "__all__"

class CaseMinSerializer(CaseBaseSerializer):
    class Meta:
        model = Case
        fields = ["orcabus_id", "name", "type"]


class CaseSerializer(CaseBaseSerializer):
    class Meta:
        model = Case
        fields = "__all__"
