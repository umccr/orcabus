# Define a dependency function that returns the pagination parameters
from fastapi import Query


def get_pagination_params(
    # offset must be greater than or equal to 0
    page_offset: int = Query(0, ge=0, alias='pageOffset'),
    # limit must be greater than 0
    page_size: int = Query(100, gt=0, alias='pageSize')
):
    return {"page_offset": page_offset, "page_size": page_size}
