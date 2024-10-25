from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from workflow_manager.models import AnalysisContext


class AnalysisContextBaseSerializer(SerializersBase):
    prefix = AnalysisContext.orcabus_id_prefix


class AnalysisContextListParamSerializer( OptionalFieldsMixin, AnalysisContextBaseSerializer):
    class Meta:
        model = AnalysisContext
        fields = "__all__"

class AnalysisContextMinSerializer(AnalysisContextBaseSerializer):
    class Meta:
        model = AnalysisContext
        fields = ["orcabus_id", "name", "usecase"]


class AnalysisContextSerializer(AnalysisContextBaseSerializer):
    class Meta:
        model = AnalysisContext
        fields = "__all__"
