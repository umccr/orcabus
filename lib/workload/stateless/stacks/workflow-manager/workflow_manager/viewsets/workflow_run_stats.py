from django.db.models import Q, Max, F
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from workflow_manager.models import WorkflowRun
from workflow_manager.serializers.workflow_run import WorkflowRunDetailSerializer, WorkflowRunCountByStatusSerializer


class WorkflowRunStatsViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = WorkflowRunDetailSerializer
    pagination_class = None  # No pagination by default
    http_method_names = ['get']
    
    def get_queryset(self):
        """
        custom queryset:
        add filter by:
        start_time, end_time : range of latest state timestamp
        is_ongoing : filter by ongoing workflow runs
        status : filter by latest state status
        
        add search terms: 
        library_id: filter by library_id
        orcabus_id: filter by orcabus_id
        """
        # default time is 0
        start_time = self.request.query_params.get('start_time', 0)
        end_time = self.request.query_params.get('end_time', 0)
        
        # get is ongoing flag
        is_ongoing = self.request.query_params.get('is_ongoing', 'false')
        
        # get status
        status = self.request.query_params.get('status', '')
        
        # get search query params
        search_params = self.request.query_params.get('search', '')
        
        # exclude the custom query params from the rest of the query params
        def exclude_params(params):
            for param in params:
                self.request.query_params.pop(param) if param in self.request.query_params.keys() else None
                
        exclude_params([
            'start_time',
            'end_time',
            'is_ongoing',
            'status',
            'search'
        ])
        
        # get all workflow runs with rest of the query params
        # add prefetch_related & select_related to reduce the number of queries
        result_set = WorkflowRun.objects.get_by_keyword(**self.request.query_params)\
                                        .prefetch_related('states')\
                                        .prefetch_related('libraries')\
                                        .select_related('workflow')
 
        if start_time and end_time:
            result_set = result_set.annotate(latest_state_time=Max('states__timestamp')).filter(
                latest_state_time__range=[start_time, end_time]
            )

        if is_ongoing.lower() == 'true':
            result_set = result_set.filter(
                ~Q(states__status="FAILED") &
                ~Q(states__status="ABORTED") &
                ~Q(states__status="SUCCEEDED") &
                ~Q(states__status="RESOLVED")
            )
        
        if status:
            result_set = result_set.annotate(latest_state_time=Max('states__timestamp')).filter(
                states__timestamp=F('latest_state_time'),
                states__status=status.upper()
            )
        
        # Combine search across multiple fields (worfkflow run name, comment, library_id, orcabus_id, workflow name)
        if search_params:
            result_set = result_set.filter(
                Q(workflow_run_name__icontains=search_params) |
                Q(comment__icontains=search_params) |
                Q(libraries__library_id__icontains=search_params) |
                Q(libraries__orcabus_id__icontains=search_params) |
                Q(workflow__workflow_name__icontains=search_params)
            ).distinct()
            
        return result_set
    
    @extend_schema(responses=WorkflowRunDetailSerializer(many=True))
    @action(detail=False, methods=['GET'], url_path='list_all')
    def list_all(self, request):
        return self.list(request)
    
    
    @extend_schema(responses=WorkflowRunCountByStatusSerializer)
    @action(detail=False, methods=['GET'])
    def count_by_status(self, request):
        """
        Returns the count of records for each status: 'SUCCEEDED', 'ABORTED', 'FAILED', and 'Onging' State based on the query params.
        """
        start_time = self.request.query_params.get('start_time', 0)
        end_time = self.request.query_params.get('end_time', 0)
        
        base_queryset = self.get_queryset()
        
        all_count = base_queryset.count()
        
        annotate_queryset = base_queryset.annotate(latest_state_time=Max('states__timestamp'))
        
        succeeded_count = annotate_queryset.filter(
            states__timestamp=F('latest_state_time'),
            states__status="SUCCEEDED"
        ).count()
        
        aborted_count = annotate_queryset.filter(
            states__timestamp=F('latest_state_time'),
            states__status="ABORTED"
        ).count()
        
        failed_count = annotate_queryset.filter(
            states__timestamp=F('latest_state_time'),
            states__status="FAILED"
        ).count()
        
        resolved_count = annotate_queryset.filter(
            states__timestamp=F('latest_state_time'),
            states__status="RESOLVED"
        ).count()
        
        ongoing_count = base_queryset.filter(
            ~Q(states__status="FAILED") &
            ~Q(states__status="ABORTED") &
            ~Q(states__status="SUCCEEDED")
        ).count()
        
        return Response({
            'all': all_count,
            'succeeded': succeeded_count,
            'aborted': aborted_count,
            'failed': failed_count,
            'resolved': resolved_count,
            'ongoing': ongoing_count
        }, status=200)
        
        