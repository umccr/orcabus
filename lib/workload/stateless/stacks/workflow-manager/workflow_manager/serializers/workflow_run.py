from rest_framework import serializers

from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import WorkflowRun, AnalysisRun
from workflow_manager.serializers.state import StateSerializer, StateMinSerializer

class WorkflowRunBaseSerializer(SerializersBase):
    prefix = WorkflowRun.orcabus_id_prefix

    # we only want to include the current state
    # all states are available via a dedicated endpoint
    current_state = serializers.SerializerMethodField()

    def get_current_state(self, obj) -> dict:
        latest_state = obj.get_latest_state()
        return StateSerializer(latest_state).data if latest_state else None


class WorkflowRunSerializer(WorkflowRunBaseSerializer):
    from .workflow import WorkflowMinSerializer
    
    workflow = WorkflowMinSerializer(read_only=True)
    class Meta:
        model = WorkflowRun
        exclude = ["libraries"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # representation['workflow'] = Workflow.orcabus_id_prefix + representation['workflow']
        if representation['analysis_run']:
            representation['analysis_run'] = AnalysisRun.orcabus_id_prefix + representation['analysis_run']
        return representation

    def get_current_state(self, obj) -> dict:
        # overwrite the default State serializer to only report the minimal information in listings
        latest_state = obj.get_latest_state()
        return StateMinSerializer(latest_state).data if latest_state else None


class WorkflowRunDetailSerializer(WorkflowRunBaseSerializer):
    from .library import LibrarySerializer
    from .workflow import WorkflowMinSerializer
    from .analysis_run import AnalysisRunSerializer

    libraries = LibrarySerializer(many=True, read_only=True)
    workflow = WorkflowMinSerializer(read_only=True)
    analysis_run = AnalysisRunSerializer(read_only=True)
    current_state = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowRun
        fields = "__all__"


class WorkflowRunCountByStatusSerializer(serializers.Serializer):
    all = serializers.IntegerField()
    succeeded = serializers.IntegerField()
    aborted = serializers.IntegerField()
    failed = serializers.IntegerField()
    resolved = serializers.IntegerField()
    ongoing = serializers.IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
