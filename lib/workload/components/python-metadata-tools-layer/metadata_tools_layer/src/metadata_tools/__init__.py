#!/usr/bin/env python

# Utils
from .utils.aws_helpers import get_orcabus_token

# Errors
from .utils.errors import (
    SampleNotFoundError,
    SubjectNotFoundError,
    ProjectNotFoundError,
    IndividualNotFoundError,
    LibraryNotFoundError,
    ContactNotFoundError,
)

# Models
from .utils.models import (
    MetadataBase,
    LibraryBase,
    SampleBase,
    SubjectBase,
    IndividualBase,
    ProjectBase,
    ContactBase,
    LibraryDetail,
    SampleDetail,
    SubjectDetail,
    IndividualDetail,
    ProjectDetail,
    ContactDetail,
    Library,
    Sample,
    Subject,
    Individual,
    Project,
    Contact,
    LimsRow,
)

# Library Helpers
from .utils.library_helpers import (
    get_library_from_library_id,
    get_library_id_from_library_orcabus_id,
    get_library_orcabus_id_from_library_id,
    get_library_from_library_orcabus_id,
    coerce_library_id_or_orcabus_id_to_library_orcabus_id,
    get_subject_from_library_id,
    get_library_type,
    get_library_assay_type,
    get_library_phenotype,
    get_library_workflow,
    get_all_libraries
)

# Sample Helpers
from .utils.sample_helpers import (
    get_sample_from_sample_id,
    get_sample_orcabus_id_from_sample_id,
    get_sample_from_sample_orcabus_id,
    list_libraries_in_sample,
    coerce_sample_id_or_orcabus_id_to_sample_orcabus_id,
    get_all_samples
)

# Subject Helpers
from .utils.subject_helpers import (
    get_subject_from_subject_id,
    get_subject_orcabus_id_from_subject_id,
    get_subject_from_subject_orcabus_id,
    coerce_subject_id_or_orcabus_id_to_subject_orcabus_id,
    list_samples_in_subject,
    list_libraries_in_subject,
    get_all_subjects
)

# Project Helpers
from .utils.project_helpers import (
    get_all_projects,
    get_project_orcabus_id_from_project_id,
    get_project_from_project_id,
    get_project_from_project_orcabus_id,
    coerce_project_id_or_orcabus_id_to_project_orcabus_id,
    list_libraries_in_project
)

# Individual Helpers
from .utils.individual_helpers import (
    get_individual_from_individual_id,
    get_individual_orcabus_id_from_individual_id,
    get_individual_from_individual_orcabus_id,
    coerce_individual_id_or_orcabus_id_to_individual_orcabus_id,
    get_all_individuals,
    list_libraries_in_individual
)

# Contact helpers
from .utils.contact_helpers import (
    get_contact_from_contact_id,
    get_contact_orcabus_id_from_contact_id,
    get_contact_from_contact_orcabus_id,
    coerce_contact_id_or_orcabus_id_to_contact_orcabus_id,
    get_all_contacts
)

# Miscell
from .utils.lims_helpers import (
    generate_lims_row,
)

# Set _all__
__all__ = [
    # Errors
    'SampleNotFoundError',
    'SubjectNotFoundError',
    'ProjectNotFoundError',
    'IndividualNotFoundError',
    'LibraryNotFoundError',
    'ContactNotFoundError',
    # Models
    'MetadataBase',
    'LibraryBase',
    'SampleBase',
    'SubjectBase',
    'IndividualBase',
    'ProjectBase',
    'ContactBase',
    'LibraryDetail',
    'SampleDetail',
    'SubjectDetail',
    'IndividualDetail',
    'ProjectDetail',
    'ContactDetail',
    'Library',
    'Sample',
    'Subject',
    'Individual',
    'Project',
    'Contact',
    'LimsRow',
    # Utils
    'get_orcabus_token',
    # Library Funcs
    'get_library_from_library_id',
    'get_library_orcabus_id_from_library_id',
    'get_library_id_from_library_orcabus_id',
    'get_library_from_library_orcabus_id',
    'get_subject_from_library_id',
    'coerce_library_id_or_orcabus_id_to_library_orcabus_id',
    'get_library_type',
    'get_library_assay_type',
    'get_library_phenotype',
    'get_library_workflow',
    'get_all_libraries',
    # Sample Funcs
    'get_sample_from_sample_id',
    'get_sample_orcabus_id_from_sample_id',
    'get_sample_from_sample_orcabus_id',
    'coerce_sample_id_or_orcabus_id_to_sample_orcabus_id',
    'list_libraries_in_sample',
    'list_samples_in_subject',
    'get_all_samples',
    # Subject Funcs
    'get_subject_from_subject_id',
    'get_subject_orcabus_id_from_subject_id',
    'get_subject_from_subject_orcabus_id',
    'coerce_subject_id_or_orcabus_id_to_subject_orcabus_id',
    'list_libraries_in_subject',
    'get_all_subjects',
    # Project Funcs
    'get_all_projects',
    'get_project_from_project_id',
    'get_project_orcabus_id_from_project_id',
    'get_project_from_project_orcabus_id',
    'coerce_project_id_or_orcabus_id_to_project_orcabus_id',
    'list_libraries_in_project',
    # Individual Funcs
    'get_individual_from_individual_id',
    'get_individual_orcabus_id_from_individual_id',
    'get_individual_from_individual_orcabus_id',
    'coerce_individual_id_or_orcabus_id_to_individual_orcabus_id',
    'get_all_individuals',
    'list_libraries_in_individual',
    # Contact Funcs
    'get_contact_from_contact_id',
    'get_contact_orcabus_id_from_contact_id',
    'get_contact_from_contact_orcabus_id',
    'coerce_contact_id_or_orcabus_id_to_contact_orcabus_id',
    'get_all_contacts',
    # Miscell
    'generate_lims_row',
]
