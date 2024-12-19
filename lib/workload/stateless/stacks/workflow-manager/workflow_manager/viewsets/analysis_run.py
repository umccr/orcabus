from drf_spectacular.utils import extend_schema

from workflow_manager.models.analysis_run import AnalysisRun
from workflow_manager.serializers.analysis_run import AnalysisRunDetailSerializer, AnalysisRunSerializer, AnalysisRunListParamSerializer
from .base import BaseViewSet


class AnalysisRunViewSet(BaseViewSet):
    serializer_class = AnalysisRunDetailSerializer  # use detailed
    search_fields = AnalysisRun.get_base_fields()
    queryset = AnalysisRun.objects.prefetch_related("libraries").all()

    @extend_schema(parameters=[
        AnalysisRunListParamSerializer,
    ])
    def list(self, request, *args, **kwargs):
        self.serializer_class = AnalysisRunSerializer  # use simple view for record listing
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params =self.request.query_params.copy()
        return AnalysisRun.objects.get_by_keyword(self.queryset, **query_params)
