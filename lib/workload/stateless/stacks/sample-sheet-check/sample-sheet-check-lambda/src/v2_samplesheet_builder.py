#!/usr/bin/env python3

"""
Steps needed:

Generate a json of the existing v1 samplesheet

Convert the json to a v2 samplesheet
"""
import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, List
from tempfile import NamedTemporaryFile
import pandas as pd

from src import camel_to_snake
from src.samplesheet import SampleSheet, check_global_override_cycles
from src.logger import get_logger
from src.globals import (
    V2_SAMPLESHEET_BCLCONVERT_ADAPTER_SETTINGS_BY_ASSAY_TYPE,
    V2_ADAPTER_SETTINGS, V2_DATA_ROWS, V2_SAMPLESHEET_GLOBAL_SETTINGS, V2_SAMPLESHEET_DATA_SETTINGS,
    V2_BCLCONVERT_BASESPACE_URN, V2_BCLCONVERT_BASESPACE_SOFTWARE_VERSION,
    EXPERIMENT_REGEX_STR
)
from v2_samplesheet_maker.functions.v2_samplesheet_writer import v2_samplesheet_writer

logger = get_logger()


def get_bclconvert_adapter_setting_by_type_and_assay(sample_type: str, sample_assay: str, setting_name: str) -> str:
    """
    This function retrieves the adapter setting for a given sample type and assay.

    Parameters:
    sample_type (str): The type of the sample.
    sample_assay (str): The assay of the sample.
    setting_name (str): The name of the setting to be retrieved.

    Returns:
    str: The value of the adapter setting for the given sample type and assay.
    """
    for key in V2_SAMPLESHEET_BCLCONVERT_ADAPTER_SETTINGS_BY_ASSAY_TYPE.keys():
        if re.match(key, f"{sample_type}:{sample_assay}"):
            setting_value = V2_SAMPLESHEET_BCLCONVERT_ADAPTER_SETTINGS_BY_ASSAY_TYPE[key].get(setting_name, None)
            if setting_value is not None:
                return setting_value
    else:
        logger.debug(f"Could not get the bclconvert settings for this type / assay combination '{sample_type}' / '{sample_assay}'")


def get_bclconvert_settings_by_library_id(library_id: str, samplesheet: SampleSheet) -> Dict:
    """
    This function retrieves the BCLConvert settings for a given library ID from a sample sheet.

    Parameters:
    library_id (str): The ID of the library.
    samplesheet (SampleSheet): The sample sheet from which to retrieve the settings.

    Returns:
    Dict: A dictionary containing the BCLConvert settings for the given library ID.
    """

    # Get metadata for library id
    library_id_metadata = samplesheet.metadata_df.query(f"library_id=='{library_id}'").squeeze()

    bclconvert_settings_dict = {
        "override_cycles": library_id_metadata["override_cycles"],
        "library_prep_kit_name": library_id_metadata["assay"]
    }

    for adapter_setting in V2_ADAPTER_SETTINGS:
        bclconvert_settings_dict.update(
            {
                adapter_setting: get_bclconvert_adapter_setting_by_type_and_assay(
                    library_id_metadata["type"],
                    library_id_metadata["assay"],
                    adapter_setting
                )
            }
        )

    return bclconvert_settings_dict


def get_samplesheet_header_dict(samplesheet: SampleSheet) -> Dict:
    """
    This function retrieves the header information from a given SampleSheet object and returns it as a dictionary.

    Parameters:
    samplesheet (SampleSheet): The SampleSheet object from which to retrieve the header information.

    Returns:
    Dict: A dictionary containing the header information from the SampleSheet object.
    """
    header_dict = dict(samplesheet.header)

    # Update FileFormatVersion
    header_dict['file_format_version'] = '2'

    # Convert Experiment Name to Run Name
    header_dict['run_name'] = header_dict.pop('Experiment Name')

    # Convert Instrument Type to instrument_type
    header_dict['instrument_type'] = header_dict.pop('Instrument Type')

    return header_dict


def get_reads_dict(samplesheet: SampleSheet) -> Dict:
    """
    This function retrieves the read cycle information from a given SampleSheet object and returns it as a dictionary.

    Parameters:
    samplesheet (SampleSheet): The SampleSheet object from which to retrieve the read cycle information.

    Returns:
    Dict: A dictionary containing the read cycle information from the SampleSheet object.
    """
    # Count the cycle list
    cycle_count_list = check_global_override_cycles(samplesheet)

    # Convert the reads list into a dict
    reads_dict = {
        "read_1_cycles": samplesheet.reads[0],
        "read_2_cycles": samplesheet.reads[-1]
    }

    # If we have dual-indexed + paired end reads, add the index cycles
    if len(cycle_count_list) == 4:
        # Confirm that we have matches between reads and cycle_count_list
        if not samplesheet.reads[0] == cycle_count_list[0] and samplesheet.reads[-1] == cycle_count_list[-1]:
            logger.warning("Got mismatch between reads in samplesheet and override cycle count list")
            logger.warning(f"'{samplesheet.reads[0]}' vs '{cycle_count_list[0]}' and "
                           f"'{samplesheet.reads[-1]}' vs '{cycle_count_list[-1]}'")
        else:
            reads_dict.update(
                {
                    "index_1_cycles": cycle_count_list[1],
                    "index_2_cycles": cycle_count_list[2]
                }
            )

    return reads_dict


def get_bclconvert_settings_dict(samplesheet: SampleSheet) -> Dict:
    """
    This function retrieves the BCLConvert settings for a given SampleSheet object.

    Parameters:
    samplesheet (SampleSheet): The SampleSheet object from which to retrieve the BCLConvert settings.

    Returns:
    Dict: A dictionary containing the BCLConvert settings for the given SampleSheet object.
    """
    # Initialise settings dictionary
    bclconvert_settings_dict = {}

    # Add global bclconvert settings
    for setting_key, setting_value in samplesheet.settings.items():
        setting_key_snake_case = camel_to_snake(setting_key)
        if setting_key_snake_case in V2_SAMPLESHEET_GLOBAL_SETTINGS.keys():
            bclconvert_settings_dict.update(
                {
                    # Coerce type
                    setting_key_snake_case: setting_value
                }
            )

    # Get BCLConvert settings by assay and type
    bclconvert_settings_list = []
    for (sample_type, sample_assay), mini_sample_df in samplesheet.metadata_df.groupby(["type", "assay"]):
        sample_bclconvert_settings = {}
        for adapter_setting in V2_SAMPLESHEET_GLOBAL_SETTINGS.keys():
            sample_bclconvert_settings.update(
                {
                    adapter_setting: get_bclconvert_adapter_setting_by_type_and_assay(
                        sample_type,
                        sample_assay,
                        adapter_setting
                    )
                }
            )

        bclconvert_settings_list.append(sample_bclconvert_settings)

    # Convert settings to a dataframe
    bclconvert_settings_df = pd.DataFrame(bclconvert_settings_list)

    # Append settings in the samplesheet
    bclconvert_settings_df = pd.concat(
        [
            bclconvert_settings_df,
            pd.DataFrame(
                [
                    pd.Series(bclconvert_settings_dict).reindex(V2_SAMPLESHEET_GLOBAL_SETTINGS.keys())
                ]
            )
        ]
    )

    # Drop empty settings
    bclconvert_settings_df = bclconvert_settings_df.dropna(
        how='all',
        axis='columns'
    )

    # Check that all global settings are uniform across all samples
    has_error = False
    bclconvert_settings_dict = {}
    for column in bclconvert_settings_df.columns.tolist():
        if not bclconvert_settings_df[column].dropna().unique().shape[0] == 1:
            logger.error(f"{column}: {bclconvert_settings_df[column].unique()}")
            has_error = True
            continue
        # Create BCLConvert settings dict
        bclconvert_settings_dict.update(
            {
                column: bclconvert_settings_df[column].dropna().unique().item()
            }
        )
    if has_error:
        raise ValueError

    # Coerce types of settings
    # Add global bclconvert settings
    for setting_key, setting_value in bclconvert_settings_dict.items():
        bclconvert_settings_dict[setting_key] = V2_SAMPLESHEET_GLOBAL_SETTINGS[setting_key](setting_value)

    # Add in BCLConvert URN
    # Add in Software Version too
    bclconvert_settings_dict["urn"] = V2_BCLCONVERT_BASESPACE_URN
    bclconvert_settings_dict["software_version"] = V2_BCLCONVERT_BASESPACE_SOFTWARE_VERSION

    # Return bclconvert settings dict
    return bclconvert_settings_dict


def get_bclconvert_data_list(samplesheet: SampleSheet) -> List:
    """
    This function retrieves the BCLConvert data list for a given SampleSheet object.

    Some hacky updates -
    1. Lowercase all keys
    2. Drop Sample_Project, and Sample_ID
    3. Rename Sample_Name (the library id) to SampleID
    4. Drop tailing N's from index and index2
    5. Drop empty columns

    Parameters:
    samplesheet (SampleSheet): The SampleSheet object from which to retrieve the BCLConvert data list.

    Returns:
    List: A list containing the BCLConvert data for the given SampleSheet object.
    """
    data_dict_list = []

    for index, data_row in samplesheet.data.iterrows():
        # Drop datadict
        data_dict = dict(data_row)

        # Add bclconvert settings
        data_dict.update(
            get_bclconvert_settings_by_library_id(
                library_id=data_dict["Sample_Name"],
                samplesheet=samplesheet
            )
        )

        # Append data dict
        data_dict_list.append(
            data_dict
        )

    # Convert to dataframe
    data_dict_list_df = pd.DataFrame(data_dict_list)

    # Some hacky updates -
    # 1. Lowercase all keys
    # 2. Drop Sample_Project, and Sample_ID
    # 3. Rename Sample_Name (the library id) to SampleID
    # 4. Drop tailing N's from index and index2
    # 5. Drop empty columns

    # Lowercase all columns
    data_dict_list_df = data_dict_list_df.rename(
        columns={
            column: column.lower()
            for column in data_dict_list_df.columns
        }
    )

    # Drop Sample_Project and Sample_ID
    data_dict_list_df = data_dict_list_df.drop(
        columns=[
            "sample_project",
            "sample_id"
        ]
    )

    # Rename Sample_Name (the library id) to SampleID
    data_dict_list_df = data_dict_list_df.rename(
        columns={
            "sample_name": "sample_id"
        }
    )

    # Select only columns in V2_DATA_ROWS
    data_dict_list_df = data_dict_list_df[
        filter(
            lambda col: col in V2_DATA_ROWS,
            data_dict_list_df.columns
        )
    ]

    # Drop tailing N's from index and index2
    for index_col in ['index', 'index2']:
        data_dict_list_df[index_col] = data_dict_list_df[index_col].str.rstrip("N")

    # Strip topup and reruns from sample id names
    data_dict_list_df["sample_id"] = data_dict_list_df["sample_id"].apply(
        lambda sample_id: re.sub(EXPERIMENT_REGEX_STR["top_up"], "", sample_id)
    )
    data_dict_list_df["sample_id"] = data_dict_list_df["sample_id"].apply(
        lambda sample_id: re.sub(EXPERIMENT_REGEX_STR["rerun"], "", sample_id)
    )

    # Convert to dataframe and drop empty columns
    data_dict_list_df = data_dict_list_df.replace(
        {
            "": pd.NA
        }
    ).dropna(
        how='all',
        axis='columns'
    )

    # Convert and return back as list
    return data_dict_list_df.to_dict(
        orient="records"
    )


def update_bclconvert_settings_on_data_list_settings(bclconvert_settings_dict: Dict, bclconvert_data_list: List) -> [Dict, pd.DataFrame]:
    """
    This function updates the BCLConvert settings based on the data list settings.

    Parameters:
    bclconvert_settings_dict (Dict): The dictionary containing the BCLConvert settings.
    bclconvert_data_list (List): The list containing the BCLConvert data.

    Returns:
    Tuple[Dict, pd.DataFrame]: A tuple containing the updated BCLConvert settings dictionary and a DataFrame of the BCLConvert data list.
    """
    # Always copy
    bclconvert_settings_dict = deepcopy(bclconvert_settings_dict)
    bclconvert_data_list = deepcopy(bclconvert_data_list)

    # Find uniform settings within BCLConvert_Data and move them to BCLConvert_Settings
    bclconvert_data_list_df = pd.DataFrame(bclconvert_data_list)
    for setting_column in V2_SAMPLESHEET_DATA_SETTINGS:
        # Check column in dataframe first
        if setting_column not in bclconvert_data_list_df.columns:
            continue
        # Move setting column to bclconvert settings dict
        if bclconvert_data_list_df[setting_column].unique().shape[0] == 1:
            # Add to bclconvert settings
            bclconvert_settings_dict[setting_column] = bclconvert_data_list_df[setting_column].unique().item()
            # Drop from data list
            bclconvert_data_list_df = bclconvert_data_list_df.drop(
                columns=setting_column
            )

    # Some items might be empty in the bclconvert settings dict, so drop them
    for setting_name, setting_value in deepcopy(bclconvert_settings_dict).items():
        if setting_value is None or setting_value == "":
            _ = bclconvert_settings_dict.pop(setting_name)

    # Drop minimum adapter overlap if no adapters are present
    if bclconvert_settings_dict.get("minimum_adapter_overlap", None) is not None:
        # Check settings
        if (
                bclconvert_settings_dict.get("adapter_read_1", None) is None and
                bclconvert_settings_dict.get("adapter_read_2", None) is None
        ) and (
                "adapter_read_1" not in bclconvert_data_list_df.columns and
                "adapter_read_2" not in bclconvert_data_list_df.columns
        ):
            logger.debug("Dropping minimum_adapter_overlap from bclconvert settings as no adapters are present")
            _ = bclconvert_settings_dict.pop("minimum_adapter_overlap")

    return bclconvert_settings_dict, bclconvert_data_list_df.to_dict(orient="records")


def v1_samplesheet_to_json(samplesheet: SampleSheet) -> Dict:
    """
    This function converts a version 1 SampleSheet object into a JSON format.

    Parameters:
    samplesheet (SampleSheet): The version 1 SampleSheet object to be converted.

    Returns:
    Dict: A dictionary representing the JSON format of the SampleSheet object.
    """
    # Get header dict
    header_dict = get_samplesheet_header_dict(samplesheet)

    # Get reads dict (and add index cycles)
    reads_dict = get_reads_dict(samplesheet)

    # Get bclconvert settings dict
    bclconvert_settings_dict = get_bclconvert_settings_dict(samplesheet)

    # Add bclconvert settings by sample id
    bclconvert_data_list = get_bclconvert_data_list(samplesheet)

    # Update bclconvert settings based on data list settings
    # For now this is removing the minimum_adapter overlap if no other adapters are present
    bclconvert_settings_dict, bclconvert_data_list = update_bclconvert_settings_on_data_list_settings(
        bclconvert_settings_dict,
        bclconvert_data_list
    )

    cloud_settings_section = {
        "generated_version": "0.0.0",
        "cloud_workflow": "ica_workflow_1"
    }

    # Write out json
    samplesheet_dict = {
        "header": header_dict,
        "reads": reads_dict,
        "bclconvert_settings": bclconvert_settings_dict,
        "bclconvert_data": bclconvert_data_list,
        "cloud_settings": cloud_settings_section
    }

    return samplesheet_dict


def build_v2_samplesheet(samplesheet_json: dict) -> str:
    """
    This function constructs a version 2 SampleSheet from a given JSON representation of a version 1 SampleSheet.

    Parameters:
    samplesheet_json (dict): A dictionary representing the JSON format of a version 1 SampleSheet object.

    Returns:
    str: A string representation of the version 2 SampleSheet.
    """

    with NamedTemporaryFile(prefix="v2_samplesheet_", suffix=".csv") as tmp_file_obj_h:
        # Write to CSV
        v2_samplesheet_writer(
            samplesheet_json,
            Path(tmp_file_obj_h.name)
        )

        # Read as str
        with open(tmp_file_obj_h.name, "r") as f_h:
            return f_h.read()


def v1_to_v2_samplesheet(samplesheet):
    """
    This function converts a version 1 SampleSheet object into a version 2 SampleSheet string.

    Parameters:
    samplesheet (SampleSheet): The version 1 SampleSheet object to be converted.

    Returns:
    str: A string representation of the version 2 SampleSheet.
    """
    try:
        # Convert to samplesheet json
        samplesheet_json = v1_samplesheet_to_json(samplesheet)

        # Build v2 samplesheet and convert to a string
        v2_samplesheet_str = build_v2_samplesheet(samplesheet_json)
    except Exception as e:
        logger.error(f"Error converting v1 to v2 samplesheet: {e}")
        raise e

    # Return samplesheet as a string
    return v2_samplesheet_str
