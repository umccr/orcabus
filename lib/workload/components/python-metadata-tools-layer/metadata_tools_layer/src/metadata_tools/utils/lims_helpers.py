#!/usr/bin/env python3

"""
Custom helpers, for use in generating a 'lims row' given a library id
"""
from typing import Dict
from .models import LimsRow


def generate_lims_row(library_id: str, instrument_run_id: str) -> LimsRow:
    """
    Generate a 'lims row' given a library id, we return the following:
    """
    from .library_helpers import get_library_from_library_id
    from .subject_helpers import get_subject_from_subject_orcabus_id
    from .individual_helpers import get_individual_from_individual_orcabus_id
    from .project_helpers import get_project_from_project_orcabus_id
    from .sample_helpers import get_sample_from_sample_orcabus_id

    library_obj = get_library_from_library_id(library_id)
    sample_obj = get_sample_from_sample_orcabus_id(library_obj['sample']['orcabusId'])
    subject_obj = get_subject_from_subject_orcabus_id(library_obj['subject']['orcabusId'])
    individual_obj = get_individual_from_individual_orcabus_id(subject_obj['individualSet'][0]['orcabusId'])
    project_obj = get_project_from_project_orcabus_id(library_obj['projectSet'][0]['orcabusId'])

    return {
        'externalSubjectId': subject_obj['subjectId'],
        'externalSampleId': sample_obj['externalSampleId'],
        'individualId': individual_obj['individualId'],
        'sampleId': sample_obj['sampleId'],
        'libraryId': library_obj['libraryId'],
        'instrumentRunId': instrument_run_id,
        'projectName': project_obj['projectId'],
        'sampleType': library_obj['type'],
        'assay': library_obj['assay'],
        'phenotype': library_obj['phenotype'],
    }
