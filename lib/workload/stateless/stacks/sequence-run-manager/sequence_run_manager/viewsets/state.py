from rest_framework.viewsets import GenericViewSet

from sequence_run_manager.models.state import State
from sequence_run_manager.serializers.state import StateSerializer


class StateViewSet(GenericViewSet):
    serializer_class = StateSerializer
    search_fields = State.get_base_fields()
    orcabus_id_prefix = State.orcabus_id_prefix
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return State.objects.filter(sequence=self.kwargs["orcabus_id"])
