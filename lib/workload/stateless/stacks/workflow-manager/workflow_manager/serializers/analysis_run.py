from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from workflow_manager.models import AnalysisRun, Analysis, AnalysisContext

class AnalysisRunBaseSerializer(SerializersBase):
    prefix = AnalysisRun.orcabus_id_prefix

class AnalysisRunListParamSerializer( OptionalFieldsMixin, AnalysisRunBaseSerializer,):
    class Meta:
        model = AnalysisRun
        fields = "__all__"

class AnalysisRunSerializer(AnalysisRunBaseSerializer):
    class Meta:
        model = AnalysisRun
        exclude = ["libraries"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['analysis'] = Analysis.orcabus_id_prefix + representation['analysis']
        if representation['storage_context']:
            representation['storage_context'] = AnalysisContext.orcabus_id_prefix + representation['storage_context']
        if representation['compute_context']:
            representation['compute_context'] = AnalysisContext.orcabus_id_prefix + representation['compute_context']
        return representation


class AnalysisRunDetailSerializer(AnalysisRunBaseSerializer):
    from .library import LibrarySerializer
    from .analysis import AnalysisSerializer
    from .analysis_context import AnalysisContextSerializer

    libraries = LibrarySerializer(many=True, read_only=True)
    analysis = AnalysisSerializer(read_only=True)
    storage_context = AnalysisContextSerializer(read_only=True)
    compute_context = AnalysisContextSerializer(read_only=True)

    class Meta:
        model = AnalysisRun
        fields = "__all__"
