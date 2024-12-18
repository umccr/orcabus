from abc import ABC
from rest_framework import filters
from django.shortcuts import get_object_or_404
from sequence_run_manager.pagination import StandardResultsSetPagination
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet


class BaseViewSet(ReadOnlyModelViewSet, ABC):
    lookup_value_regex = "[^/]+"  # This is to allow for special characters in the URL
    ordering_fields = "__all__"
    ordering = ["-orcabus_id"]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
