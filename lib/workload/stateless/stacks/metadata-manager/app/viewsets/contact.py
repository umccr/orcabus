from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from app.models import Contact
from app.serializers.contact import ContactSerializer, ContactDetailSerializer, ContactHistorySerializer

from .base import BaseViewSet


class ContactViewSet(BaseViewSet):
    serializer_class = ContactDetailSerializer
    search_fields = Contact.get_base_fields()
    queryset = Contact.objects.prefetch_related('project_set').all()
    orcabus_id_prefix = Contact.orcabus_id_prefix

    @extend_schema(parameters=[
        ContactSerializer
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        query_params = self.get_query_params()
        return Contact.objects.get_by_keyword(**query_params)

    @extend_schema(responses=ContactHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(ContactHistorySerializer)
