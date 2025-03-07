from drf_spectacular.utils import extend_schema

from case_manager.models.case import Case
from case_manager.serializers.case import CaseSerializer, CaseListParamSerializer
from case_manager.viewsets.base import BaseViewSet

class CaseViewSet(BaseViewSet):
    serializer_class = CaseSerializer
    search_fields = Case.get_base_fields()

    @extend_schema(parameters=[
        CaseListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        query_params = self.get_query_params()
        return Case.objects.get_by_keyword(self.queryset, **query_params)
