from typing import Optional, List, Dict

from fastapi import Query, HTTPException

from . import JobStatus
from datetime import datetime, timedelta


class BaseQueryParameters:
    def __init__(self):
        self.validate_query()

    def validate_query(self):
        raise NotImplementedError("Subclasses must implement validate_query")



class PackageQueryParameters(BaseQueryParameters):
    def __init__(
            self,
            # Package name
            package_name: Optional[str] = Query(
                None,
                description="The name of the package to filter by"
            ),
            package_name_list: Optional[List[str]] = Query(
                None,
                alias="packageName[]",
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
            requested_after: Optional[datetime] = Query(
                None,
                alias="requestAfter",
                description="The date and time after which the package was requested"
            ),
            requested_before: Optional[datetime] = Query(
                None,
                alias="requestBefore",
                description="The date and time before which the package was requested"
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
        self.package_name = package_name
        self.package_name_list = package_name_list

        # Initialise status query parameters
        self.status = status
        self.status_list = status_list

        # Initialise creation time query parameters
        self.requested_after = requested_after
        self.requested_before = requested_before

        # Initialise completion time query parameters
        self.completed_after = completed_after
        self.completed_before = completed_before

        # Call the super constructor to validate the query
        super().__init__()

    def validate_query(self):
        # Assert that only one of fastq_id and fastq_id_list is specified
        if self.package_name is not None and self.package_name_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of packageName or packageName[] is allowed"
            )

        if self.package_name is not None:
            self.package_name_list = [self.package_name]

        # Assert that only one of status and status_list is specified
        if self.status is not None and self.status_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of status or status[] is allowed"
            )
        if self.status is not None:
            self.status_list = [self.status]

        # Assert that requested_after and requested_before are valid datetime strings
        for attr in ["requested_after", "requested_before", "completed_after", "completed_before"]:
            value = getattr(self, attr)
            if value is not None:
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{attr} must be a valid datetime string"
                    )
        # Assert that if requested_after is specified
        # and requested_before is specfied, that requested_after is less than requested_before
        if self.requested_after is not None and self.requested_before is not None:
            if self.requested_after > self.requested_before:
                raise HTTPException(
                    status_code=400,
                    detail="createdAfter must be less than createdBefore"
                )
        # Assert that if requested_after is specified it is less than the current time
        if self.requested_after is not None:
            if datetime.now() < self.requested_after:
                raise HTTPException(
                    status_code=400,
                    detail="createdAfter must be less than the current time"
                )
        # Assert that 'createdBefore' is within the last two weeks since we delete jobs older than that
        if self.requested_before is not None:
            if (datetime.now() - timedelta(days=14)) > self.requested_before:
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

        # Assert that if both of requested_after and completed_before are specified,
        # requested_after is less than completed_before
        if self.requested_after is not None and self.completed_before is not None:
            if self.requested_after > self.completed_before:
                raise HTTPException(
                    status_code=400,
                    detail="createdAfter must be less than completedBefore"
                )
        # Assert that if both of requested_before and completed_after are specified,
        # requested_before is less than completed_after
        if self.requested_before is not None and self.completed_after is not None:
            if self.requested_before > self.completed_after:
                raise HTTPException(
                    status_code=400,
                    detail="createdBefore must be less than completedAfter"
                )


    def to_params_dict(self) -> Dict[str, str]:
        for attr in [
            "package_name_list",
            "status_list",
            "requested_after",
            "requested_before",
            "completed_after",
            "completed_before"
        ]:
            value = getattr(self, attr)
            if value is not None:
                return {
                    f"{attr.replace('_list', '[]')}": ','.join(map(str, value))
                }
        return {}


class PushQueryParameters(BaseQueryParameters):
    def __init__(
            self,
            # Package id
            package_id: Optional[str] = Query(
                None,
                alias="packageId",
                description="The ID of the package to filter by"
            ),
            package_id_list: Optional[List[str]] = Query(
                None,
                alias="packageId[]",
                description=None,
                include_in_schema=False,
                strict=False
            ),
            # Package name
            package_name: Optional[str] = Query(
                None,
                alias="packageName",
                description="The name of the package to filter by"
            ),
            package_name_list: Optional[List[str]] = Query(
                None,
                alias="packageName[]",
                description="The list of package names to filter by",
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
        # Initialise package query parameters
        self.package_id = package_id
        self.package_id_list = package_id_list
        self.package_name = package_name
        self.package_name_list = package_name_list

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
        # Assert that only one of package_name and package_name_list is specified
        if self.package_name is not None and self.package_name_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of packageName or packageName[] is allowed"
            )

        if self.package_name is not None:
            self.package_name_list = [self.package_name]

        # Assert that only one of package_id and package_id_list is specified
        if self.package_id is not None and self.package_id_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of packageId or packageId[] is allowed"
            )
        if self.package_id is not None:
            self.package_id_list = [self.package_id]

        # Now assert that only one of package_id and package_name is specified
        if self.package_id_list is not None and self.package_name_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of packageId or packageName is allowed"
            )

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
            "package_id_list",
            "package_name_list",
            "status_list",
            "created_after",
            "created_before",
            "completed_after",
            "completed_before",
        ]:
            value = getattr(self, attr)
            if value is not None:
                return {
                    f"{attr.replace('_list', '[]')}": ','.join(map(str, value))
                }
        return {}