#!/usr/bin/env python3

"""
Query helpers -

get_fastqs_in_instrument_run_id

get_fastqs_in_library

get_fastqs_in_sample

get_fastqs_in_subject

get_fastqs_in_individual

get_fastqs_in_project

get_fastq_by_rgid_and_instrument_run_id

"""
from typing import List

from .request_helpers import (
    get_request_response_results,
)

from .globals import FASTQ_LIST_ROW_ENDPOINT, FASTQ_SET_ENDPOINT
from .models import FastqListRow, FastqSet


def get_fastq(fastq_id: str, **kwargs) -> FastqListRow:
    return get_request_response_results(f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}", params=kwargs)


def get_fastq_set(fastq_set_id: str, **kwargs) -> FastqSet:
    """
    Get the fastq set by id
    :param fastq_set_id:
    :param kwargs:
    :return:
    """
    return get_request_response_results(f"{FASTQ_SET_ENDPOINT}/{fastq_set_id}", params=kwargs)


def get_fastqs(*args, **kwargs) -> List[FastqListRow]:
    """
    Get all fastqs
    """
    return get_request_response_results(FASTQ_LIST_ROW_ENDPOINT, params=kwargs)


def get_fastqs_in_instrument_run_id(instrument_run_id: str):
    """
    Get all fastqs in an instrument run id
    """
    return get_fastqs(
        **{
            "instrumentRunId": instrument_run_id
        }
    )


def get_fastqs_in_library(library_id: str):
    """
    Get all fastqs in a library
    """
    return get_fastqs(
        **{
            "library": library_id
        }
    )


def get_fastqs_in_library_list(library_id_list: List[str]):
    """
    Get all fastqs in a list of libraries
    """
    return get_fastqs(
        **{
            "library[]": library_id_list
        }
    )


def get_fastqs_in_libraries_and_instrument_run_id(library_id_list, instrument_run_id):
    """
    Get all fastqs in a list of libraries and instrument run id
    :param library_id_list:
    :param instrument_run_id:
    :return:
    """
    return get_fastqs(
        **{
            "library[]": library_id_list,
            "instrumentRunId": instrument_run_id
        }
    )


def get_fastqs_in_sample(sample_id):
    """
    Get all fastqs in a sample
    """
    return get_fastqs(
        **{
            "sample": sample_id
        }
    )


def get_fastqs_in_subject(subject_id):
    """
    Get all fastqs in a subject
    """
    return get_fastqs(
        **{
            "subject": subject_id
        }
    )


def get_fastqs_in_individual(individual_id):
    """
    Get all fastqs in an individual
    """
    return get_fastqs(
        **{
            "individual": individual_id
        }
    )


def get_fastqs_in_project(project_id):
    """
    Get all fastqs in a project
    """
    return get_fastqs(
        **{
            "project": project_id
        }
    )


def get_fastq_list_rows_in_fastq_set(fastq_set_id):
    """
    Get all fastqs in a fastq set
    """
    return get_fastqs(
        **{
            "fastqSet": fastq_set_id
        }
    )