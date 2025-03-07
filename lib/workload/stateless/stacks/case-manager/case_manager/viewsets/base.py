from abc import ABC
from rest_framework import filters
from django.shortcuts import get_object_or_404
from case_manager.pagination import StandardResultsSetPagination
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet


class BaseViewSet(ReadOnlyModelViewSet, ABC):
    lookup_value_regex = "[^/]+"  # This is to allow for special characters in the URL
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def get_query_params(self):
        # TODO: remove ?
        query_params = self.request.query_params.copy()
        return query_params
