from drf_spectacular.utils import extend_schema
from sequence_run_manager.viewsets.base import BaseViewSet
from django.db.models import Q
from sequence_run_manager.models import Sequence
from sequence_run_manager.serializers.sequence import SequenceSerializer, SequenceListParamSerializer, \
    SequenceMinSerializer


class SequenceViewSet(BaseViewSet):
    serializer_class = SequenceSerializer
    search_fields = Sequence.get_base_fields()

    def get_queryset(self):
        """Pick up the start_time and end_time from the query params and exclude them from the rest of the query params"""
        
        start_time = self.request.query_params.get('start_time', 0)
        end_time = self.request.query_params.get('end_time', 0)
        
         # exclude the custom query params from the rest of the query params
        def exclude_params(params):
            for param in params:
                self.request.query_params.pop(param) if param in self.request.query_params.keys() else None
                
        exclude_params([
            'start_time',
            'end_time',
        ])
        result_set = Sequence.objects.get_by_keyword(**self.request.query_params)

        if start_time and end_time:
            result_set = result_set.filter(Q(start_time__range=[start_time, end_time]) | Q(end_time__range=[start_time, end_time]))

        return result_set
    

    @extend_schema(parameters=[
        SequenceListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        self.serializer_class = SequenceMinSerializer
        return super().list(request, *args, **kwargs)
