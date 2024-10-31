from django.db.models import Q, Max, F
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from workflow_manager.models import WorkflowRun
from workflow_manager.serializers.workflow_run import WorkflowRunDetailSerializer


class WorkflowRunStatsViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = WorkflowRunDetailSerializer
    pagination_class = None  # No pagination by default
    http_method_names = ['get']
    
    def get_queryset(self):
        """
        Returns all workflow runs for statistical analysis without pagination.
        """
        # default time is 0
        start_time = self.request.query_params.get('start_time', 0)
        end_time = self.request.query_params.get('end_time', 0)
        
        # exclude the custom query params from the rest of the query params
        query_params = self.request.query_params.copy()
        for param in ['start_time', 'end_time']:
            query_params.pop(param, None)
            
        # Base queryset with optimized joins
        result_set = WorkflowRun.objects.get_by_keyword(**query_params)\
                                    .prefetch_related('states', 'libraries')\
                                    .select_related('workflow')
        print(start_time, end_time)
        if start_time and end_time:
            result_set = result_set.annotate(latest_state_time=Max('states__timestamp'))\
                                 .filter(latest_state_time__range=[start_time, end_time])
        
        return result_set
    