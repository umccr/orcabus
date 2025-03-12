#!/usr/bin/env python3

"""
SFN LAMBDA PLACEHOLDER: __get_file_from_s3_object_id_lambda_function_arn__
Get file from the s3 object id
"""

import typing
from pathlib import Path
from typing import Dict, Optional
# Layer tools
from metadata_tools import get_library_from_library_orcabus_id, Library
from workflow_tools import (
    get_workflow_run_from_portal_run_id, WorkflowRun
)
from filemanager_tools import (
    FileObject,
    get_file_object_from_id
)
from fastq_tools import get_fastqs_in_library

if typing.TYPE_CHECKING:
    from s3_json_tools import FileObjectWithMetadataTypeDef


def handler(event, context) -> Dict[str, FileObject]:
    """
    Handler function for getting file from the s3 object id
    """

    # Get the s3 object id from the event
    s3_object_id = event.get('s3ObjectId')

    # Get the file object from the s3 object id
    file_object: 'FileObject' = get_file_object_from_id(s3_object_id)

    # Get workflow from the file object
    workflow_run: WorkflowRun = get_workflow_run_from_portal_run_id(
        file_object['attributes']['portalRunId']
    )

    # Get the library id from the workflow run linked libraries list
    if len(workflow_run['libraries']) == 0:
        raise ValueError('No linked libraries found in the workflow run')

    # If there is more than one library id, collect the tumor library id
    if len(workflow_run['libraries']) > 1:
        library: Optional['Library'] = None
        for library_iter_ in workflow_run['libraries']:
            library_obj: Library = get_library_from_library_orcabus_id(library_iter_['orcabusId'])
            if library_obj['phenotype'] == 'tumor':
                library = library_iter_
                break
        else:
            raise ValueError('No tumor library found in the workflow run, but multiple libraries in the run')
    else:
        library: 'Library' = workflow_run['libraries'][0]

    # Get the relative path for the primary file
    if file_object['key'].endswith(".fastq.gz") or file_object['key'].endswith(".fastq.ora"):
        # Get all fastqs for this library (again) and then match on the s3 ingest id
        fastq_obj = next(filter(
            lambda fastq_obj_iter_: file_object['ingestId'] in list(filter(
                lambda s3_ingest_id_iter: s3_ingest_id_iter is not None,
                [
                    fastq_obj_iter_['readSet']['r1']['s3IngestId'],
                    # R2 is an optional item in the readSet
                    fastq_obj_iter_['readSet'].get('r2', {}).get('s3IngestId', None)
                ]
            )),
            get_fastqs_in_library(library['orcabusId'])
        ))

        # Get the instrument run id
        instrument_run_id = fastq_obj['instrumentRunId']

        # Get the relative path
        relative_path = Path('fastq') / instrument_run_id / workflow_run['portalRunId'] / Path(file_object['key']).name

    else:
        # Get the relative path for the secondary file
        relative_path = Path(workflow_run['workflow']['workflowName']) / workflow_run['portalRunId']


    # Convert to a file object with metadata attributes
    file_object_with_metadata: 'FileObjectWithMetadataTypeDef' = file_object.copy()
    file_object_with_metadata.update(
        {
            'library': library,
            'workflowRun': workflow_run,
            'relativePath': relative_path
        }
    )

    return {
        'fileObject': file_object_with_metadata
    }
