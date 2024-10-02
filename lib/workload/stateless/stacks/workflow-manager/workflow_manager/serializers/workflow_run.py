from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import WorkflowRun, Workflow, AnalysisRun


class WorkflowRunBaseSerializer(SerializersBase):
    prefix = WorkflowRun.orcabus_id_prefix


class WorkflowRunSerializer(WorkflowRunBaseSerializer):
    class Meta:
        model = WorkflowRun
        exclude = ["libraries"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['workflow'] = Workflow.orcabus_id_prefix + representation['workflow']
        if representation['analysis_run']:
            representation['analysis_run'] = AnalysisRun.orcabus_id_prefix + representation['analysis_run']
        return representation


class WorkflowRunDetailSerializer(WorkflowRunBaseSerializer):
    from .library import LibrarySerializer
    from .workflow import WorkflowMinSerializer
    from .analysis_run import AnalysisRunSerializer
    from .state import StateSerializer

    libraries = LibrarySerializer(many=True, read_only=True)
    workflow = WorkflowMinSerializer(read_only=True)
    analysis_run = AnalysisRunSerializer(read_only=True)
    state_set = StateSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRun
        fields = "__all__"
