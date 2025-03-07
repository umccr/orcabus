
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django.utils import timezone

from case_manager.models import State, Case
from case_manager.serializers.state import StateSerializer


class StateViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin,  GenericViewSet):
    serializer_class = StateSerializer
    search_fields = State.get_base_fields()
    http_method_names = ['get', 'post', 'patch']
    pagination_class = None

    def get_queryset(self):
        return State.objects.filter(case_run=self.kwargs["orcabus_id"])
    
    def create(self, request, *args, **kwargs):
        case_orcabus_id = self.kwargs.get("orcabus_id")
        case_run = Case.objects.get(orcabus_id=case_orcabus_id)

        # Check if the case run has a "Failed" or "Aborted" state
        latest_state = case_run.get_latest_state()
        if latest_state.status not in ["FAILED"]:
            return Response({"detail": "Can only create 'Resolved' state for case runs with 'Failed' states."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if the new state is "Resolved"
        if request.data.get('status', '').upper() != "RESOLVED":
            return Response({"detail": "Can only create 'Resolved' state."},
                            status=status.HTTP_400_BAD_REQUEST)

        # comment is required when status is "Resolved"
        if not request.data.get('comment'):
            return Response({"detail": "Comment is required when status is 'Resolved'."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        
        # Prepare data for serializer
        data = request.data.copy()
        data['timestamp'] = timezone.now()
        data['case_run'] = case_orcabus_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(case_run_id=self.kwargs["orcabus_id"], status="RESOLVED")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if the state being updated is "Resolved"
        if instance.status != "RESOLVED":
            return Response({"detail": "Can only update 'Resolved' state records."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if only the comment field is being updated
        if set(request.data.keys()) != {'comment'}:
            return Response({"detail": "Only the comment field can be updated."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save(status="RESOLVED")
