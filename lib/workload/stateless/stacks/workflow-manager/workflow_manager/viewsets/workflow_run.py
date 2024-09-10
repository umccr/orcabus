from django.db.models import Q, Max
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet

from workflow_manager.models.workflow_run import WorkflowRun
from workflow_manager.pagination import StandardResultsSetPagination
from workflow_manager.serializers import WorkflowRunModelSerializer


class WorkflowRunViewSet(ReadOnlyModelViewSet):
    serializer_class = WorkflowRunModelSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = '__all__'
    ordering = ['-id']
    search_fields = WorkflowRun.get_base_fields()

    def get_queryset(self):
        
        """
        custom queryset to filter by:
        start_time, end_time : range of latest state timestamp
        is_ongoing : filter by ongoing workflow runs
        """
        # default time is 0
        start_time = self.request.query_params.get('start_time', 0)
        end_time = self.request.query_params.get('end_time', 0)
        
        # get is ongoing flag
        is_ongoing = self.request.query_params.get('is_ongoing', 'false')
        
        # exclude the custom query params from the rest of the query params
        def exclude_params(params):
            for param in params:
                self.request.query_params.pop(param) if param in self.request.query_params.keys() else None
                
        exclude_params([
            'start_time',
            'end_time',
            'is_ongoing'
        ])
                
        # get all workflow runs with rest of the query params
        result_set = WorkflowRun.objects.get_by_keyword(**self.request.query_params).prefetch_related('states').prefetch_related('libraries').select_related('workflow') # add prefetch_related & select_related to reduce the number of queries
 
        if start_time and end_time:
            result_set = result_set.annotate(latest_state_time=Max('states__timestamp')).filter(
                latest_state_time__range=[start_time, end_time]
            )

        if is_ongoing.lower() == 'true':
            result_set = result_set.filter(
                ~Q(states__status="FAILED") &
                ~Q(states__status="ABORTED") &
                ~Q(states__status="SUCCEEDED")
            )
        
        return result_set

    @action(detail=False, methods=['GET'])
    def ongoing(self, request):
        # Get all books marked as favorite
        print(request)
        print(self.request.query_params)
        ordering = self.request.query_params.get('ordering', '-id')

        if "status" in self.request.query_params.keys():
            print("found status!")
            status = self.request.query_params.get('status')
            result_set = WorkflowRun.objects.get_by_keyword(states__status=status).order_by(ordering)
        else:
            result_set = WorkflowRun.objects.get_by_keyword(**self.request.query_params).order_by(ordering)

        result_set = result_set.filter(
            ~Q(states__status="FAILED") &
            ~Q(states__status="ABORTED") &
            ~Q(states__status="SUCCEEDED")
        )
        pagw_qs = self.paginate_queryset(result_set)
        serializer = self.get_serializer(pagw_qs, many=True)
        return self.get_paginated_response(serializer.data)
