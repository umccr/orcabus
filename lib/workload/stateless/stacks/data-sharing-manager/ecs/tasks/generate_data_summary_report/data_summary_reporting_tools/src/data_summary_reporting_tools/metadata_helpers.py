# Imports
from typing import List
from pandera.typing import DataFrame, Series

from .models import LibraryModel, LibraryBase


def get_library_id_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['libraryId']

def get_sample_id_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['sample']['sampleId']


def get_external_sample_id_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['sample']['externalSampleId']


def get_subject_id_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['subject']['subjectId']


def get_individual_id_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['subject']['individualSet'][0]['individualId']


def get_project_id_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['projectSet'][0]['projectId']


def get_assay_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['assay']

def get_type_from_library_model(
        library_row: Series[LibraryModel]
) -> str:
    return library_row.to_dict()['type']


def get_metadata_attribute_from_libraries_list(
        libraries_list: List[LibraryBase],
        library_df: DataFrame[LibraryModel],
        metadata_attribute: str
) -> List[str]:
    library_rows = get_library_rows_from_analysis_libraries_list(
       libraries_list,
       library_df
    )
    functions_dict = {
        "libraryId": get_library_id_from_library_model,
        "sampleId": get_sample_id_from_library_model,
        "externalSampleId": get_external_sample_id_from_library_model,
        "subjectId": get_subject_id_from_library_model,
        "individualId": get_individual_id_from_library_model,
        "projectId": get_project_id_from_library_model,
        'assay': get_assay_from_library_model,
        'type': get_type_from_library_model
    }
    if metadata_attribute not in functions_dict:
        raise ValueError("Could not find function for metadata attribute: " + metadata_attribute)
    return list(map(
        lambda library_row_iter_: functions_dict[metadata_attribute](library_row_iter_),
        library_rows
    ))



def get_library_row(
        library_id: str,
        library_df: DataFrame[LibraryModel],
) -> Series[LibraryModel]:
    return library_df.query(
        f"libraryId=='{library_id}'"
    ).squeeze()


def get_library_rows_from_analysis_libraries_list(
        libraries_list: List[LibraryBase],
        library_df: DataFrame[LibraryModel]
) -> List[Series[LibraryModel]]:
    return list(filter(
        lambda library_row_iter_: (
            library_row_iter_ is not None and
            (not library_row_iter_.shape[0] == 0)
        ),
        list(map(
            lambda library_base_iter_: get_library_row(
                library_id=library_base_iter_['libraryId'],
                library_df=library_df
            ),
            libraries_list
        ))
    ))
