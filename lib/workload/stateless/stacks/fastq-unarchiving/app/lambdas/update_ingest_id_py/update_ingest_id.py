#!/usr/bin/env python3

"""
Update the ingest id using the filemanager tools api

Use the filemanager tools layer to update the ingest id for a file.

We have to do this for each file in the ingest.

"""
from typing import Dict, List
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from fastq_tools import get_fastq, FastqListRow
from filemanager_tools import update_ingest_id, get_file_object_from_s3_uri


def get_read_set_file_objects_from_fastq_obj(fastq_obj: FastqListRow) -> List[Dict[str, str]]:
    return list(filter(
        lambda read_set_iter_: read_set_iter_ is not None,
        [
            fastq_obj['readSet']['r1'],
            fastq_obj['readSet'].get('r2', None)
        ]
    ))


def file_name_in_file_obj_list(file_obj_list: List[Dict[str, str]], file_name: str) -> bool:
    return any(
        map(
            lambda file_obj_iter_: Path(urlparse(file_obj_iter_['s3Uri']).path).name == file_name,
            file_obj_list
        )
    )


def file_name_in_fastq_obj(fastq_obj: Dict[str, str], file_name: str) -> bool:
    """
    Get the s3 uris from the fastq object and check if the file name is in the list.
    :param fastq_obj:
    :param file_name:
    :return:
    """
    return file_name_in_file_obj_list(
        get_read_set_file_objects_from_fastq_obj(fastq_obj),
        file_name
    )


def handler(event, context) -> Dict[str, bool]:
    """
    Not a trivial task, we first need to match the ingest id to the file id
    and then update the ingest id for the file.
    Therefore we get all fastqIds from the top-level map, and to match to the bucket, key prefix provided in the bottom-level map.
    :param event:
    :param context:
    :return:
    """
    fastq_ids = event["fastqIds"]
    bucket = event['bucket']
    key = event['key']
    file_name = Path(urlparse(key).path).name

    try:
        fastq_obj = next(filter(
            lambda fastq_id_iter_: file_name_in_fastq_obj(get_fastq(fastq_id_iter_), file_name),
            fastq_ids
        ))
    except StopIteration:
        raise ValueError(f"Could not find fastqId for file {file_name}")

    # Get the ingest id from the s3 uri
    read_file_object = next(filter(
        lambda read_file_iter_: file_name_in_file_obj_list(read_file_iter_, read_file_iter_['s3Uri']),
        get_read_set_file_objects_from_fastq_obj(fastq_obj)
    ))

    # Get the ingest id from the fastq manager
    fastq_manager_ingest_id = read_file_object['ingestId']

    # Get the file id from the file manager
    file_manager_file_object = get_file_object_from_s3_uri(
        str(urlunparse(("s3", bucket, key, None, None, None)))
    )
    file_manager_ingest_id = file_manager_file_object['ingestId']

    # Check if the ingest ids match
    ingest_id_updated_complete = False
    if fastq_manager_ingest_id != file_manager_ingest_id:
        ingest_id_updated_complete = True
        update_ingest_id(file_manager_file_object['s3ObjectId'], fastq_manager_ingest_id)

    return {
        "ingestIdUpdatedComplete": ingest_id_updated_complete
    }
