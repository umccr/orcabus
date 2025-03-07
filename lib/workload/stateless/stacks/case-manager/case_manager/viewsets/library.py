from drf_spectacular.utils import extend_schema

from case_manager.models.library import Library
from case_manager.viewsets.base import BaseViewSet
from case_manager.serializers.library import LibrarySerializer


class LibraryViewSet(BaseViewSet):
    serializer_class = LibrarySerializer
    search_fields = Library.get_base_fields()

    @extend_schema(parameters=[
        LibrarySerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        query_params = self.get_query_params()
        qs = Library.objects.filter(caserun=self.kwargs["case_id"]) # TODO: fix
        return Library.objects.get_by_keyword(qs, **query_params)
