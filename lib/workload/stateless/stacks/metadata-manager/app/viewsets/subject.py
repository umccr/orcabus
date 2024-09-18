from drf_spectacular.utils import extend_schema
from rest_framework import filters

from app.models import Subject
from app.serializers.subject import SubjectDetailSerializer
from app.pagination import StandardResultsSetPagination
from .base import BaseViewSet


class SubjectViewSet(BaseViewSet):
    serializer_class = SubjectDetailSerializer
    search_fields = Subject.get_base_fields()
    queryset = Subject.objects.prefetch_related('individual_set').all()
    orcabus_id_prefix = Subject.orcabus_id_prefix

    @extend_schema(parameters=[
        SubjectDetailSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Subject.objects.get_by_keyword(self.queryset, **self.request.query_params)
