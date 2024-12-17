from abc import ABC

from drf_spectacular.utils import extend_schema
from rest_framework.mixins import DestroyModelMixin

from app.pagination import StandardResultsSetPagination

from django.shortcuts import get_object_or_404

from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from app.viewsets.utils import get_email_from_jwt


class BaseViewSet(ModelViewSet, ABC):
    lookup_value_regex = "[^/]+"  # This is to allow for special characters in the URL
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    http_method_names = ['get', 'patch', 'delete']

    def retrieve_history(self, history_serializer):
        """
        To use this as API routes, you need to call it from the child class and put the appropriate decorator.

        e.g.
        @extend_schema(responses=LibraryHistorySerializer(many=True), description="Retrieve the history of this model")
        @action(detail=True, methods=['get'], url_name='history', url_path='history')
        def retrieve_history(self, request, *args, **kwargs):
            return super().retrieve_history(LibraryHistorySerializer)

        Args:
            history_serializer (serializers.Serializer): The serializer for the history data.

        Returns:
            Response: A Response with the paginated, serialized history data.
        """

        # Grab the PK object from the queryset
        pk = self.kwargs.get('pk')

        obj = get_object_or_404(self.queryset, pk=pk)

        history_qs = obj.history.all()
        page = self.paginate_queryset(history_qs)
        serializer = history_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)


    def perform_destroy(self, instance):
        """
        The perform_destroy method is overridden to allow for the _history_user to be set.
        """
        requester_email = get_email_from_jwt(self.request)
        if not requester_email:
            raise ValueError("The requester email is not found in the JWT token.")

        instance._history_user = requester_email
        super().perform_destroy(instance)


    def perform_update(self, serializer):
        """
        The perform_destroy method is overridden to allow for the _history_user to be set.
        """
        requester_email = get_email_from_jwt(self.request)
        if not requester_email:
            raise ValueError("The requester email is not found in the JWT token.")

        serializer._history_user = requester_email
        super().perform_update(serializer)

    def perform_create(self, serializer):
        """
        The perform_create method is overridden to allow for the _history_user to be set.
        """
        requester_email = get_email_from_jwt(self.request)
        if not requester_email:
            raise ValueError("The requester email is not found in the JWT token.")

        serializer._history_user = requester_email
        super().perform_create(serializer)
