from drf_spectacular.utils import extend_schema

from workflow_manager.models.analysis import Analysis
from workflow_manager.serializers.analysis import AnalysisDetailSerializer, AnalysisSerializer, AnalysisListParamSerializer
from .base import BaseViewSet


class AnalysisViewSet(BaseViewSet):
    serializer_class = AnalysisDetailSerializer  # use detailed serializer as default
    search_fields = Analysis.get_base_fields()
    queryset = Analysis.objects.prefetch_related("contexts").prefetch_related("workflows").all()

    @extend_schema(parameters=[
        AnalysisListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        self.serializer_class = AnalysisSerializer  # use simple serializer for list view
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.request.query_params.copy()
        return Analysis.objects.get_by_keyword(self.queryset, **query_params)
