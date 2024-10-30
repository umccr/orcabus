from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from workflow_manager.models import AnalysisRun

class AnalysisRunBaseSerializer(SerializersBase):
    prefix = AnalysisRun.orcabus_id_prefix

class AnalysisRunListParamSerializer( OptionalFieldsMixin, AnalysisRunBaseSerializer,):
    class Meta:
        model = AnalysisRun
        fields = "__all__"
class AnalysisRunListParamSerializer( OptionalFieldsMixin, AnalysisRunBaseSerializer,):
    class Meta:
        model = AnalysisRun
        fields = "__all__"

class AnalysisRunSerializer(AnalysisRunBaseSerializer):
    from .analysis import AnalysisMinSerializer
    from .analysis_context import AnalysisContextMinSerializer
    
    analysis = AnalysisMinSerializer(read_only=True)
    storage_context = AnalysisContextMinSerializer(read_only=True)
    compute_context = AnalysisContextMinSerializer(read_only=True)
    class Meta:
        model = AnalysisRun
        exclude = ["libraries"]



class AnalysisRunDetailSerializer(AnalysisRunBaseSerializer):
    from .library import LibrarySerializer
    from .analysis import AnalysisDetailSerializer
    from .analysis_context import AnalysisContextSerializer

    libraries = LibrarySerializer(many=True, read_only=True)
    analysis = AnalysisDetailSerializer(read_only=True)
    storage_context = AnalysisContextSerializer(read_only=True)
    compute_context = AnalysisContextSerializer(read_only=True)

    class Meta:
        model = AnalysisRun
        fields = "__all__"
