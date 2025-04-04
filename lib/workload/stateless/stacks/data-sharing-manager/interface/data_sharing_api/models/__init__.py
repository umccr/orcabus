# Standard models

from typing import TypedDict, Optional, List, Any, ClassVar, Self, Dict
from enum import Enum
from urllib.parse import urlparse, urlunparse
from ..globals import DEFAULT_ROWS_PER_PAGE
import typing

from pydantic import BaseModel


class LibraryDict(TypedDict):
    orcabusId: Optional[str]
    libraryId: Optional[str]


class SecondaryAnalysisDict(TypedDict):
    orcabusId: Optional[str]
    portalRunId: Optional[str]
    workflowRunName: Optional[str]


class FastqDict(TypedDict):
    orcabusId: Optional[str]
    sampleId: Optional[str]
    fileName: Optional[str]
    instrumentRunId: Optional[str]
    lane: Optional[str]
    fileSize: Optional[str]


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    SUCCEEDED = "SUCCEEDED"


class JobPatch(BaseModel):
    status: JobStatus
    errorMessage: Optional[str] = None


class QueryPagination(TypedDict):
    page: Optional[int]
    rowsPerPage: Optional[int]


class Links(TypedDict):
    previous: Optional[str]
    next: Optional[str]


class ResponsePagination(QueryPagination):
    count: int


class QueryPaginatedResponse(BaseModel):
    """
    Job Query Response, includes a list of jobs, the total
    """
    links: Links
    pagination: ResponsePagination
    results: List[Any]
    # Implemented in subclass
    url_placeholder: ClassVar[str] = None

    def resolve_url_placeholder(self, **kwargs) -> str:
        raise NotImplementedError

    @classmethod
    def from_results_list(cls, results: List[Any], query_pagination: QueryPagination, params_response: Dict, **kwargs) -> Self:
        # From pagination calculate the links
        if cls.url_placeholder is None:
            raise ValueError("URL must be set for QueryPaginatedResponse")
        url_obj = urlparse(cls.resolve_url_placeholder(**kwargs))

        query_pagination = {
            'page': query_pagination.get('page', 1),
            'rowsPerPage': query_pagination.get('rowsPerPage', DEFAULT_ROWS_PER_PAGE)
        }

        response_pagination: ResponsePagination = dict(
            **query_pagination,
            # Add in count using the results length
            **{
                'count': len(results)
            }
        )

        if query_pagination['page'] == 1:
            previous_page = None
        else:
            params_response_prev = params_response.copy()
            params_response_prev['page'] = query_pagination['page'] - 1
            params_str = "&".join([
                f"{k}={v}"
                for k, v in params_response_prev.items()
            ])

            previous_page = str(urlunparse(
                (url_obj.scheme, url_obj.netloc, url_obj.path, None, params_str, None)
            ))

        if ( response_pagination['page'] * response_pagination['rowsPerPage'] ) >= response_pagination['count']:
            next_page = None
        else:
            params_response_next = params_response.copy()
            params_response_next['page'] = query_pagination['page'] + 1
            params_str = "&".join([
                f"{k}={v}"
                for k, v in params_response_next.items()
            ])
            next_page = str(urlunparse(
                (url_obj.scheme, url_obj.netloc, url_obj.path, None, params_str, None)
            ))

        # Calculate the start and end of the results
        results_start = ( query_pagination['page'] - 1 ) * query_pagination['rowsPerPage']
        results_end = results_start + query_pagination['rowsPerPage']

        # Generate the response object
        return cls(
            links={
                'previous': previous_page,
                'next': next_page
            },
            pagination=response_pagination,
            results=results[results_start:results_end]
        )

    if typing.TYPE_CHECKING:
        def model_dump(self, **kwargs) -> 'Self':
            pass