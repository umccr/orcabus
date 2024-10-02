from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from workflow_manager.models.workflow_run import WorkflowRun
from workflow_manager.serializers.workflow_run import WorkflowRunDetailSerializer, WorkflowRunSerializer
from workflow_manager.viewsets.base import BaseViewSet


class WorkflowRunViewSet(BaseViewSet):
    serializer_class = WorkflowRunDetailSerializer
    search_fields = WorkflowRun.get_base_fields()
    queryset = WorkflowRun.objects.prefetch_related("state_set").prefetch_related("libraries").all()
    orcabus_id_prefix = WorkflowRun.orcabus_id_prefix

    @extend_schema(parameters=[
        WorkflowRunSerializer
    ])
    def list(self, request, *args, **kwargs):
        self.serializer_class = WorkflowRunSerializer  # use simple view for record listing
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return WorkflowRun.objects.get_by_keyword(self.queryset, **query_params)

    @action(detail=False, methods=['GET'])
    def ongoing(self, request):
        self.serializer_class = WorkflowRunSerializer  # use simple view for record listing
        # Get all books marked as favorite
        print(request)
        print(self.request.query_params)
        ordering = self.request.query_params.get('ordering', '-orcabus_id')

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
