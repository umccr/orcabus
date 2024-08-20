from abc import ABC

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings


class PaginationConstant(ABC):
    ROWS_PER_PAGE = "rows_per_page"
    PAGE = "page"
    COUNT = "count"


class StandardResultsSetPagination(PageNumberPagination):
    page_size = api_settings.PAGE_SIZE
    page_size_query_param = PaginationConstant.ROWS_PER_PAGE
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "pagination": {
                    PaginationConstant.COUNT: self.page.paginator.count,
                    PaginationConstant.PAGE: self.page.number,
                    PaginationConstant.ROWS_PER_PAGE: self.get_page_size(self.request),
                },
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            'required': ['links', 'pagination', 'results'],
            "properties": {
                "links": {
                    "type": "object",
                    "properties": {
                        "next": {"type": "string", "format": "uri", "nullable": True,
                                 'example': 'http://api.example.org/accounts/?{page_query_param}=4'.format(
                                     page_query_param=self.page_query_param)},
                        "previous": {"type": "string", "format": "uri", "nullable": True,
                                     'example': 'http://api.example.org/accounts/?{page_query_param}=2'.format(
                                         page_query_param=self.page_query_param)},
                    },
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        PaginationConstant.COUNT: {"type": "integer"},
                        PaginationConstant.PAGE: {"type": "integer"},
                        PaginationConstant.ROWS_PER_PAGE: {"type": "integer"},
                    },
                },
                "results": schema
            },
        }
