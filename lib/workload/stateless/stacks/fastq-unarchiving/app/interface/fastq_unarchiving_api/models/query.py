from typing import Optional, List, Dict

from fastapi import Query, HTTPException

from . import JobStatus
from datetime import datetime, timedelta


class BaseQueryParameters:
    def __init__(self):
        self.validate_query()

    def validate_query(self):
        raise NotImplementedError("Subclasses must implement validate_query")



class JobQueryParameters(BaseQueryParameters):
    def __init__(
            self,
            # Fastq id
            fastq_id: Optional[str] = Query(
                None,
                alias="fastqId",
                description="The fastq ID to filter by, use <code>fastqId[]</code> for multiple values"
            ),
            fastq_id_list: Optional[List[str]] = Query(
                None,
                alias="fastqId[]",
                description=None,
                include_in_schema=False,
                strict=False
            ),
            # Status query
            status: Optional[JobStatus] = Query(
                None,
                description="The status to filter by, use <code>status[]</code> for multiple values"
            ),
            status_list: Optional[List[JobStatus]] = Query(
                None,
                alias="status[]",
                description=None,
                include_in_schema=False,
                strict=False
            ),
            # Created Time queries
            created_after: Optional[datetime] = Query(
                None,
                alias="createdAfter",
                description="The date and time after which the job was created"
            ),
            created_before: Optional[datetime] = Query(
                None,
                alias="createdBefore",
                description="The date and time before which the job was created"
            ),
            # Completion Time queries
            completed_after: Optional[datetime] = Query(
                None,
                alias="completedAfter",
                description="The date and time after which the job was completed"
            ),
            completed_before: Optional[datetime] = Query(
                None,
                alias="completedBefore",
                description="The date and time before which the job was completed"
            ),

    ):
        # Initialise fastq query parameters
        self.fastq_id = fastq_id
        self.fastq_id_list = fastq_id_list

        # Initialise status query parameters
        self.status = status
        self.status_list = status_list

        # Initialise creation time query parameters
        self.created_after = created_after
        self.created_before = created_before

        # Initialise completion time query parameters
        self.completed_after = completed_after
        self.completed_before = completed_before

        # Call the super constructor to validate the query
        super().__init__()

    def validate_query(self):
        # Assert that only one of fastq_id and fastq_id_list is specified
        if self.fastq_id is not None and self.fastq_id_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of fastqId or fastqId[] is allowed"
            )

        if self.fastq_id is not None:
            self.fastq_id_list = [self.fastq_id]

        # Assert that only one of status and status_list is specified
        if self.status is not None and self.status_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of status or status[] is allowed"
            )
        if self.status is not None:
            self.status_list = [self.status]

        # Assert that created_after and created_before are valid datetime strings
        for attr in ["created_after", "created_before", "completed_after", "completed_before"]:
            value = getattr(self, attr)
            if value is not None:
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{attr} must be a valid datetime string"
                    )
        # Assert that if created_after is specified
        # and created_before is specfied, that created_after is less than created_before
        if self.created_after is not None and self.created_before is not None:
            if self.created_after > self.created_before:
                raise HTTPException(
                    status_code=400,
                    detail="createdAfter must be less than createdBefore"
                )
        # Assert that if created_after is specified it is less than the current time
        if self.created_after is not None:
            if datetime.now() < self.created_after:
                raise HTTPException(
                    status_code=400,
                    detail="createdAfter must be less than the current time"
                )
        # Assert that 'createdBefore' is within the last two weeks since we delete jobs older than that
        if self.created_before is not None:
            if (datetime.now() - timedelta(days=14)) > self.created_before:
                raise HTTPException(
                    status_code=400,
                    detail="createdBefore must be less than the current time"
                )

        # Assert that if completed_after is specified it is less than the current time
        if self.completed_after is not None:
            if datetime.now() < self.completed_after:
                raise HTTPException(
                    status_code=400,
                    detail="completedAfter must be less than the current time"
                )

        # Assert that if completed_before is specified it is less than completed_after
        if self.completed_after is not None and self.completed_before is not None:
            if self.completed_after > self.completed_before:
                raise HTTPException(
                    status_code=400,
                    detail="completedAfter must be less than completedBefore"
                )

        # Assert that if both of created_after and completed_before are specified,
        # created_after is less than completed_before
        if self.created_after is not None and self.completed_before is not None:
            if self.created_after > self.completed_before:
                raise HTTPException(
                    status_code=400,
                    detail="createdAfter must be less than completedBefore"
                )
        # Assert that if both of created_before and completed_after are specified,
        # created_before is less than completed_after
        if self.created_before is not None and self.completed_after is not None:
            if self.created_before > self.completed_after:
                raise HTTPException(
                    status_code=400,
                    detail="createdBefore must be less than completedAfter"
                )


    def to_params_dict(self) -> Dict[str, str]:
        for attr in [
            "fastq_id_list",
            "status_list",
            "created_after",
            "created_before",
            "completed_after",
            "completed_before"
        ]:
            value = getattr(self, attr)
            if value is not None:
                return {
                    f"{attr.replace('_list', '[]')}": ','.join(map(str, value))
                }
        return {}
