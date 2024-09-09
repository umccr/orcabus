from django.db.models import Q
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
        return WorkflowRun.objects.get_by_keyword(**self.request.query_params).prefetch_related('states').prefetch_related('library_association__library') # add prefetch_related to reduce the number of queries

    @action(detail=False, methods=['GET'])
    def ongoing(self, request):
        # Get all books marked as favorite
        print(request)
        print(self.request.query_params)
        ordering = self.request.query_params.get('ordering', '-id')

        if "status" in self.request.query_params.keys():
            print("found status!")
            status = self.request.query_params.get('status')
            result_set = WorkflowRun.objects.get_by_keyword(state__status=status).order_by(ordering)
        else:
            result_set = WorkflowRun.objects.get_by_keyword(**self.request.query_params).order_by(ordering)

        result_set = result_set.filter(
            ~Q(state__status="FAILED") &
            ~Q(state__status="ABORTED") &
            ~Q(state__status="SUCCEEDED")
        )
        pagw_qs = self.paginate_queryset(result_set)
        serializer = self.get_serializer(pagw_qs, many=True)
        return self.get_paginated_response(serializer.data)
