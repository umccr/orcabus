from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import AnalysisRun, Analysis, AnalysisContext


class AnalysisRunBaseSerializer(SerializersBase):
    prefix = AnalysisRun.orcabus_id_prefix


class AnalysisRunSerializer(AnalysisRunBaseSerializer):
    class Meta:
        model = AnalysisRun
        exclude = ["libraries"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['analysis'] = Analysis.orcabus_id_prefix + representation['analysis']
        if representation['project_context']:
            representation['project_context'] = AnalysisContext.orcabus_id_prefix + representation['project_context']
        if representation['approval_context']:
            representation['approval_context'] = AnalysisContext.orcabus_id_prefix + representation['approval_context']
        return representation


class AnalysisRunDetailSerializer(AnalysisRunBaseSerializer):
    from .library import LibrarySerializer
    from .analysis import AnalysisSerializer
    from .analysis_context import AnalysisContextSerializer

    libraries = LibrarySerializer(many=True, read_only=True)
    analysis = AnalysisSerializer(read_only=True)
    approval_context = AnalysisContextSerializer(read_only=True)
    project_context = AnalysisContextSerializer(read_only=True)

    class Meta:
        model = AnalysisRun
        fields = "__all__"
