from drf_spectacular.utils import extend_schema

from case_manager.models import CaseData
from case_manager.serializers.case_data import CaseDataSerializer, CaseDataListParamSerializer
from case_manager.viewsets.base import BaseViewSet


class CaseDataViewSet(BaseViewSet):
    serializer_class = CaseDataSerializer
    search_fields = CaseData.get_base_fields()

    @extend_schema(parameters=[
        CaseDataListParamSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return CaseData.objects.get_by_keyword(self.queryset, **query_params)
