# SampleNotFoundError
from typing import Optional


class SampleNotFoundError(Exception):
    def __init__(
            self,
            sample_id: Optional[str] = None,
            sample_orcabus_id: Optional[str] = None
    ):
        self.sample_id = sample_id
        self.sample_orcabus_id = sample_orcabus_id
        if sample_id is not None:
            self.message = f"Could not find sample with id '{sample_id}'"
        elif sample_orcabus_id is not None:
            self.message = f"Could not find sample with OrcaBus ID '{sample_orcabus_id}'"
        else:
            self.message = "Could not find sample"
        super().__init__(self.message)


class SubjectNotFoundError(Exception):
    def __init__(
            self,
            subject_id: Optional[str] = None,
            subject_orcabus_id: Optional[str] = None
    ):
        self.subject_id = subject_id
        self.subject_orcabus_id = subject_orcabus_id
        if subject_id is not None:
            self.message = f"Could not find subject with id '{subject_id}'"
        elif subject_orcabus_id is not None:
            self.message = f"Could not find subject with OrcaBus ID '{subject_orcabus_id}'"
        else:
            self.message = "Could not find subject"
        super().__init__(self.message)


class ProjectNotFoundError(Exception):
    def __init__(
            self,
            project_id: Optional[str] = None,
            project_orcabus_id: Optional[str] = None
    ):
        self.project_id = project_id
        self.project_orcabus_id = project_orcabus_id
        if project_id is not None:
            self.message = f"Could not find project with id '{project_id}'"
        elif project_orcabus_id is not None:
            self.message = f"Could not find project with OrcaBus ID '{project_orcabus_id}'"
        else:
            self.message = "Could not find project"
        super().__init__(self.message)


class IndividualNotFoundError(Exception):
    def __init__(
            self,
            individual_id: Optional[str] = None,
            individual_orcabus_id: Optional[str] = None
    ):
        self.individual_id = individual_id
        self.individual_orcabus_id = individual_orcabus_id
        if individual_id is not None:
            self.message = f"Could not find individual with id '{individual_id}'"
        elif individual_orcabus_id is not None:
            self.message = f"Could not find individual with OrcaBus ID '{individual_orcabus_id}'"
        else:
            self.message = "Could not find individual"
        super().__init__(self.message)


class LibraryNotFoundError(Exception):
    def __init__(
            self,
            library_id: Optional[str] = None,
            library_orcabus_id: Optional[str] = None
    ):
        self.library_id = library_id
        self.library_orcabus_id = library_orcabus_id
        if library_id is not None:
            self.message = f"Could not find library with id '{library_id}'"
        elif library_orcabus_id is not None:
            self.message = f"Could not find library with OrcaBus ID '{library_orcabus_id}'"
        else:
            self.message = "Could not find library"
        super().__init__(self.message)


class ContactNotFoundError(Exception):
    def __init__(
            self,
            contact_id: Optional[str] = None,
            contact_orcabus_id: Optional[str] = None
    ):
        self.contact_id = contact_id
        self.contact_orcabus_id = contact_orcabus_id
        if contact_id is not None:
            self.message = f"Could not find contact with id '{contact_id}'"
        elif contact_orcabus_id is not None:
            self.message = f"Could not find contact with OrcaBus ID '{contact_orcabus_id}'"
        else:
            self.message = "Could not find contact"
        super().__init__(self.message)