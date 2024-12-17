from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer
from rest_framework.decorators import action
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django.utils import timezone

from workflow_manager.models import State, WorkflowRun
from workflow_manager.serializers.state import StateSerializer


class StateViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin,  GenericViewSet):
    serializer_class = StateSerializer
    search_fields = State.get_base_fields()
    http_method_names = ['get', 'post', 'patch']
    pagination_class = None
    
    """
    valid_states_map for state creation, update
    refer: 
        "Resolved" -- https://github.com/umccr/orcabus/issues/593
        "Deprecated" -- https://github.com/umccr/orcabus/issues/695
    """
    valid_states_map = {
        'RESOLVED': ['FAILED'],
        'DEPRECATED': ['SUCCEEDED']
    }

    def get_queryset(self):
        return State.objects.filter(workflow_run=self.kwargs["orcabus_id"])
    
    @extend_schema(responses=OpenApiTypes.OBJECT, description="Valid states map for new state creation, update")
    @action(detail=False, methods=['get'], url_name='valid_states_map', url_path='valid_states_map')
    def get_valid_states_map(self, request, **kwargs):
        return Response(self.valid_states_map)
    
    def create(self, request, *args, **kwargs):
        """
        Create a customed new state for a workflow run.
        Currently we support "Resolved", "Deprecated"
        """
        wfr_orcabus_id = self.kwargs.get("orcabus_id")
        workflow_run = WorkflowRun.objects.get(orcabus_id=wfr_orcabus_id)

        latest_state = workflow_run.get_latest_state()
        if not latest_state:
            return Response({"detail": "No state found for workflow run '{}'".format(wfr_orcabus_id)},
                            status=status.HTTP_400_BAD_REQUEST)
        latest_status = latest_state.status
        request_status = request.data.get('status', '').upper()
        
        # check if the state status is valid
        if not self.check_state_status(latest_status, request_status):
            return Response({"detail": "Invalid state request. Can't add state '{}' to '{}'".format(request_status, latest_status)},
                            status=status.HTTP_400_BAD_REQUEST)

        # comment is required when request change state
        if not request.data.get('comment'):
            return Response({"detail": "Comment is required when request status is '{}'".format(request_status)},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare data for serializer
        data = request.data.copy()
        data['timestamp'] = timezone.now()
        data['workflow_run'] = wfr_orcabus_id
        data['status'] = request_status
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if the state being updated is "Resolved"
        if instance.status not in self.valid_states_map:
            return Response({"detail": "Invalid state status."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if only the comment field is being updated
        if set(request.data.keys()) != {'comment'}:
            return Response({"detail": "Only the comment field can be updated."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

        
    def check_state_status(self, current_status, request_status):
        """
        check if the state status is valid: 
        valid_states_map[request_state] == current_state.status
        """
        if request_status not in self.valid_states_map:
            return False
        if current_status not in self.valid_states_map[request_status]:
            return False
        return True