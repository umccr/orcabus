from abc import ABC
from rest_framework import filters
from django.shortcuts import get_object_or_404
from workflow_manager.pagination import StandardResultsSetPagination
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
        print("DEBUG: pk")
        print(pk)
        if pk and pk.startswith(self.orcabus_id_prefix):
            pk = pk[len(self.orcabus_id_prefix):]

        print("DEBUG: self.queryset")
        print(self.queryset)
        print(self.get_queryset())
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def get_query_params(self):
        """
        Sanitize query params if needed
        e.g. remove prefixes for each orcabus_id
        """
        query_params = self.request.query_params.copy()
        orcabus_id = query_params.getlist("orcabus_id", None)
        if orcabus_id:
            id_list = []
            for key in orcabus_id:
                if key.startswith(self.orcabus_id_prefix):
                    id_list.append(key[len(self.orcabus_id_prefix):])
                else:
                    id_list.append(key)
            query_params.setlist('orcabus_id', id_list)

        return query_params
