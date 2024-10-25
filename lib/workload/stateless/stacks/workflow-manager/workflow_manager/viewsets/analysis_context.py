from drf_spectacular.utils import extend_schema

from workflow_manager.models.analysis_context import AnalysisContext
from workflow_manager.serializers.analysis_context import AnalysisContextSerializer, AnalysisContextListParamSerializer
from .base import BaseViewSet


class AnalysisContextViewSet(BaseViewSet):
    serializer_class = AnalysisContextSerializer
    search_fields = AnalysisContext.get_base_fields()
    orcabus_id_prefix = AnalysisContext.orcabus_id_prefix

    @extend_schema(parameters=[
        AnalysisContextListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        query_params = self.get_query_params()
        return AnalysisContext.objects.get_by_keyword(self.queryset, **query_params)
