from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin, OrcabusIdSerializerMetaMixin
from workflow_manager.models import Analysis, Workflow, AnalysisContext


class AnalysisBaseSerializer(SerializersBase):
    pass


class AnalysisListParamSerializer(OptionalFieldsMixin, AnalysisBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Analysis
        fields = "__all__"


class AnalysisMinSerializer(AnalysisBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Analysis
        fields = ["orcabus_id", "analysis_name", "analysis_version", 'status']


class AnalysisSerializer(AnalysisBaseSerializer):
    """
    Serializer to define a default representation of an Analysis record,
    mainly used in record listings.
    """

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Analysis
        fields = "__all__"
        # exclude = ["contexts", "workflows"]



class AnalysisDetailSerializer(AnalysisBaseSerializer):
    """
    Serializer to define a detailed representation of an Analysis record,
    mainly used in individual record views.
    """
    from .analysis_context import AnalysisContextSerializer
    from .workflow import WorkflowMinSerializer

    contexts = AnalysisContextSerializer(many=True, read_only=True)
    workflows = WorkflowMinSerializer(many=True, read_only=True)

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Analysis
        fields = "__all__"
