from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from sequence_run_manager.viewsets.base import BaseViewSet
from django.db.models import Q
from sequence_run_manager.models import Sequence, LibraryAssociation
from sequence_run_manager.serializers.sequence_run import SequenceRunSerializer, SequenceRunListParamSerializer, SequenceRunMinSerializer


class SequenceRunViewSet(BaseViewSet):
    serializer_class = SequenceRunSerializer
    search_fields = Sequence.get_base_fields()
    queryset = Sequence.objects.all()
    lookup_value_regex = "[^/]+" # to allow id prefix

    def get_queryset(self):
        """
        custom query params:
        start_time: start time of the sequence run
        end_time: end time of the sequence run
        
        library_id: library id of the sequence run
        """
        
        start_time = self.request.query_params.get('start_time', 0)
        end_time = self.request.query_params.get('end_time', 0)
        library_id = self.request.query_params.get('library_id', 0)
        
        # exclude the custom query params from the rest of the query params
        def exclude_params(params):
            for param in params:
                self.request.query_params.pop(param) if param in self.request.query_params.keys() else None
                
        exclude_params([
            'start_time',
            'end_time',
            'library_id',
        ])
        result_set = Sequence.objects.get_by_keyword(**self.request.query_params).distinct().filter(status__isnull=False) # filter out fake sequence runs

        if start_time and end_time:
            result_set = result_set.filter(Q(start_time__range=[start_time, end_time]) | Q(end_time__range=[start_time, end_time]))
        if library_id:
            sequence_ids = LibraryAssociation.objects.filter(library_id=library_id).values_list('sequence_id', flat=True)
            result_set = result_set.filter(orcabus_id__in=sequence_ids)

        return result_set.distinct()
    

    @extend_schema(parameters=[
        SequenceRunListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        self.serializer_class = SequenceRunMinSerializer
        return super().list(request, *args, **kwargs)
