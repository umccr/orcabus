from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import Analysis, Workflow, AnalysisContext


class AnalysisBaseSerializer(SerializersBase):
    prefix = Analysis.orcabus_id_prefix


class AnalysisSerializer(AnalysisBaseSerializer):
    """
    Serializer to define a default representation of an Analysis record,
    mainly used in record listings.
    """
    class Meta:
        model = Analysis
        fields = "__all__"
        # exclude = ["contexts", "workflows"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        new_workflow_refs = []  # Rewrite internal OrcaBUs
        for item in representation["workflows"]:
            new_workflow_refs.append(f"{Workflow.orcabus_id_prefix}{item}")
        representation["workflows"] = new_workflow_refs
        new_context_refs = []
        for item in representation["contexts"]:
            new_context_refs.append(f"{AnalysisContext.orcabus_id_prefix}{item}")
        representation["contexts"] = new_context_refs
        return representation


class AnalysisDetailSerializer(AnalysisBaseSerializer):
    """
    Serializer to define a detailed representation of an Analysis record,
    mainly used in individual record views.
    """
    from .analysis_context import AnalysisContextSerializer
    from .workflow import WorkflowMinSerializer

    contexts = AnalysisContextSerializer(many=True, read_only=True)
    workflows = WorkflowMinSerializer(many=True, read_only=True)

    class Meta:
        model = Analysis
        fields = "__all__"
