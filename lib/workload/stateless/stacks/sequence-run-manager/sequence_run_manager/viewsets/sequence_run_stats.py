from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from django.db import models
from django.db.models import Q

from sequence_run_manager.models.sequence import Sequence
from sequence_run_manager.serializers.sequence import SequenceRunCountByStatusSerializer


class SequenceStatsViewSet(GenericViewSet):
    """
    ViewSet for sequence-related statistics
    """
    @extend_schema(responses=SequenceRunCountByStatusSerializer)
    @action(detail=False, methods=['GET'])
    def status_counts(self, request):
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
        
        # Start with base queryset
        qs = Sequence.objects.all()
        
        # Apply time range filters if provided
        if start_time and end_time:
            qs = qs.filter(
                Q(start_time__range=[start_time, end_time]) |
                Q(end_time__range=[start_time, end_time])
            )

        # Get total count
        total = qs.count()
        
        # Get counts by status
        status_counts = qs.values('status').annotate(count=models.Count('status'))
        
        # Convert to dictionary with default 0 for missing statuses
        counts = {
            'all': total,
            'started': 0,
            'succeeded': 0,
            'aborted': 0,
            'failed': 0,
        }
        
        for item in status_counts:
            status = item['status'].lower()
            counts[status] = item['count']
                
        return Response(counts, status=200)

    # You can add more stats endpoints here in the future
    # For example:
    
    # @action(detail=False, methods=['GET'])
    # def monthly_trends(self, request):
    #     """Example: Get sequence counts by month"""
    #     pass
    
    # @action(detail=False, methods=['GET'])
    # def instrument_stats(self, request):
    #     """Example: Get stats grouped by instrument"""
    #     pass
