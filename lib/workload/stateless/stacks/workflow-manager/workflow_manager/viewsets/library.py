from drf_spectacular.utils import extend_schema

from workflow_manager.models.library import Library
from workflow_manager.viewsets.base import BaseViewSet
from workflow_manager.serializers.library import LibrarySerializer


class LibraryViewSet(BaseViewSet):
    serializer_class = LibrarySerializer
    search_fields = Library.get_base_fields()
    orcabus_id_prefix = Library.orcabus_id_prefix

    @extend_schema(parameters=[
        LibrarySerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        qs = Library.objects.filter(workflowrun=self.kwargs["workflowrun_id"])
        return Library.objects.get_by_keyword(qs, **query_params)
