from abc import ABC
from rest_framework import filters
from django.shortcuts import get_object_or_404
from app.pagination import StandardResultsSetPagination
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet


class BaseViewSet(ReadOnlyModelViewSet, ABC):
    lookup_value_regex = "[^/]+"  # This is to allow for special characters in the URL
    orcabus_id_prefix = ''
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]

    def retrieve(self, request, *args, **kwargs):
        """
        Since we have custom orcabus_id prefix for each model, we need to remove the prefix before retrieving it.
        """
        pk = self.kwargs.get('pk')
        if pk and pk.startswith(self.orcabus_id_prefix):
            pk = pk[len(self.orcabus_id_prefix):]

        obj = get_object_or_404(self.queryset, pk=pk)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def get_query_params(self):
        """
        Sanitize query params if needed
        e.g. remove prefixes for each orcabus_id
        """
        query_params = self.request.query_params.copy()
        orcabus_id = query_params.get("orcabus_id", None)
        if orcabus_id and orcabus_id.startswith(self.orcabus_id_prefix):
            query_params['orcabus_id'] = orcabus_id[len(self.orcabus_id_prefix):]
        return query_params
