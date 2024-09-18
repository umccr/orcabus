from drf_spectacular.utils import extend_schema
from rest_framework import filters

from app.models import Contact
from app.serializers.contact import ContactSerializer
from app.pagination import StandardResultsSetPagination

from .base import BaseViewSet


class ContactViewSet(BaseViewSet):
    serializer_class = ContactSerializer
    search_fields = Contact.get_base_fields()
    queryset = Contact.objects.all()
    orcabus_id_prefix = Contact.orcabus_id_prefix

    @extend_schema(parameters=[
        ContactSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Contact.objects.get_by_keyword(**self.request.query_params)
