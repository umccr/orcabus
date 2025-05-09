from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from sequence_run_manager.models import State, Sequence
from sequence_run_manager.serializers.state import StateSerializer


class StateViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin,  GenericViewSet):
    serializer_class = StateSerializer
    search_fields = State.get_base_fields()
    http_method_names = ['get', 'post', 'patch']
    pagination_class = None
    lookup_value_regex = "[^/]+" # to allow id prefix

    """
    valid_states_map for state creation, update
    refer: 
        "Resolved" -- https://github.com/umccr/orcabus/issues/879
    """
    valid_states_map = {
        'RESOLVED': ['FAILED']
    }

    def get_queryset(self):
        return State.objects.filter(sequence=self.kwargs["orcabus_id"])
    
    def create(self, request, *args, **kwargs):
        """
        Create a customed new state for a sequence run.
        Currently we support "Resolved"
        """
        sequence_orcabus_id = self.kwargs.get("orcabus_id")
        sequence = Sequence.objects.get(orcabus_id=sequence_orcabus_id)
        
        latest_status = sequence.status
        request_status = request.data.get('status', '').upper()
        
        print(f"latest_status: {latest_status}, request_status: {request_status}")
        # check if the state status is valid
        if not self.check_state_status(latest_status, request_status):
            return Response({"detail": "Invalid state request. Can't add state '{}' to '{}'".format(request_status, latest_status)},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # comment is required when request change state
        if not request.data.get('comment'):
            return Response({"detail": "Comment is required when request status is '{}'".format(request_status)},
                            status=status.HTTP_400_BAD_REQUEST)
            
        # create a new state
        new_state = State.objects.create(
            sequence=sequence,
            status=request_status,
            comment=request.data.get('comment'),
            timestamp=timezone.now()
        )
        
        # update the sequence status
        sequence.status = request_status
        sequence.save()
        
        # return the new state
        serializer = self.get_serializer(new_state)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        
    def update(self, request, *args, **kwargs):
        """
        Update a state for a sequence run.
        Currently we support "Resolved"
        """
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
        valid_states_map[request_state] in current_state.status
        """
        if request_status not in self.valid_states_map:
            return False
        if current_status not in self.valid_states_map[request_status]:
            return False
        return True
        
        
        
        
