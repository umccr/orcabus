from drf_spectacular.utils import extend_schema

from sequence_run_manager.viewsets.base import BaseViewSet
from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.serializers.sequence import SequenceSerializer, SequenceListParamSerializer, \
    SequenceMinSerializer


class SequenceViewSet(BaseViewSet):
    serializer_class = SequenceSerializer
    search_fields = Sequence.get_base_fields()

    def get_queryset(self):
        return Sequence.objects.get_by_keyword(**self.request.query_params)

    @extend_schema(parameters=[
        SequenceListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        self.serializer_class = SequenceMinSerializer
        return super().list(request, *args, **kwargs)
