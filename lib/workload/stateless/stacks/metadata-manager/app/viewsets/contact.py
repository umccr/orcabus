from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from app.models import Contact
from app.serializers.contact import ContactSerializer, ContactDetailSerializer, ContactHistorySerializer

from .base import BaseViewSet


class ContactViewSet(BaseViewSet):
    serializer_class = ContactSerializer
    search_fields = Contact.get_base_fields()
    queryset = Contact.objects.all()

    def get_queryset(self):
        query_params = self.request.query_params.copy()
        return Contact.objects.get_by_keyword(**query_params)

    @extend_schema(responses=ContactDetailSerializer(many=False))
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = ContactDetailSerializer
        self.queryset = Contact.objects.prefetch_related('project_set').all()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            ContactSerializer
        ],
        responses=ContactDetailSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.serializer_class = ContactDetailSerializer
        self.queryset = Contact.objects.prefetch_related('project_set').all()
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=ContactHistorySerializer(many=True), description="Retrieve the history of this model")
    @action(detail=True, methods=['get'], url_name='history', url_path='history')
    def retrieve_history(self, request, *args, **kwargs):
        return super().retrieve_history(ContactHistorySerializer)
