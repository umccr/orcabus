from drf_spectacular.utils import extend_schema
from rest_framework import filters

from app.models import Contact
from app.serializers.contact import ContactSerializer
from app.pagination import StandardResultsSetPagination

from rest_framework.viewsets import ReadOnlyModelViewSet


class ContactViewSet(ReadOnlyModelViewSet):
    lookup_value_regex = "[^/]+"
    serializer_class = ContactSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    search_fields = Contact.get_base_fields()
    queryset = Contact.objects.none()

    @extend_schema(parameters=[
        ContactSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Contact.objects.get_by_keyword(**self.request.query_params)
