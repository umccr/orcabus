#!/usr/bin/env python3

"""
Handle the workflow session object

The BCLConversion complete object looks something like this:

{
  "project_id": "a1234567-1234-1234-1234-1234567890ab",
  "analysis_id": "b1234567-1234-1234-1234-1234567890ab",
  "portal_run_id": "20240207abcduuid"
}

# FIXME - bring back samplesheet - we might want this to return to the workflow as a json object

"""

# Imports
import json
from io import StringIO
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse
import pandas as pd
from bssh_manager_tools.utils.samplesheet_helper import read_v2_samplesheet
from wrapica.enums import DataType
import logging

# Wrapica imports
from wrapica.libica_models import ProjectData
from wrapica.project_data import (
    get_project_data_obj_by_id,
    read_icav2_file_contents_to_string, get_project_data_folder_id_from_project_id_and_path,
    convert_project_id_and_data_path_to_icav2_uri, convert_project_data_obj_to_icav2_uri
)

# Local imports
from bssh_manager_tools.utils.manifest_helper import generate_run_manifest, get_dest_uri_from_src_uri
from bssh_manager_tools.utils.sample_helper import get_fastq_list_paths_from_bssh_output_and_fastq_list_csv
from bssh_manager_tools.utils.directory_helper import (
    get_basespace_run_id_from_bssh_json_output,
    generate_bclconvert_output_folder_path, get_dest_project_id_from_ssm_parameter
)
from bssh_manager_tools.utils.aws_ssm_helpers import set_icav2_env_vars
from bssh_manager_tools.utils.icav2_analysis_helpers import (
    get_bssh_json_file_id_from_analysis_output_list,
    get_run_info_xml_file_id_analysis_output_list,
    get_fastq_list_csv_file_id_from_analysis_output_list, get_run_folder_obj_from_analysis_id,
    get_interop_files_from_run_folder, get_bclconvert_outputs_from_analysis_id,
    get_samplesheet_path_from_analysis_output_list, get_samplesheet_file_id_from_analysis_output_list
)
from bssh_manager_tools.utils.xml_helpers import parse_runinfo_xml, get_run_id_from_run_info_xml_dict
from bssh_manager_tools.utils.logger import set_basic_logger

# Set logger
logger = set_basic_logger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Read in the event and collect the workflow session details
    """
    # Set ICAv2 configuration from secrets
    logger.info("Setting icav2 env vars from secrets manager")
    set_icav2_env_vars()

    # Get the BCLConvert analysis ID
    logger.info("Collecting ids from the workflow session event")
    project_id = event['project_id']
    analysis_id = event['analysis_id']
    portal_run_id = event['portal_run_id']

    # Get the input run inputs
    logger.info("Collecting input run data objects")
    input_run_folder_obj: ProjectData = get_run_folder_obj_from_analysis_id(
        project_id=project_id,
        analysis_id=analysis_id
    )

    # Get the interop files
    interop_files = get_interop_files_from_run_folder(
        input_run_folder_obj
    )

    # Get the analysis output path
    logger.info("Collecting output data objects")
    bclconvert_output_folder_id, bclconvert_output_data_list = get_bclconvert_outputs_from_analysis_id(
        project_id=project_id,
        analysis_id=analysis_id
    )

    # Get the output folder object
    logger.info("Get bclconvert output folder object")
    bclconvert_output_folder_obj = get_project_data_obj_by_id(
        project_id=project_id,
        data_id=bclconvert_output_folder_id
    )

    # Get the bssh_json
    logger.info("Collecting bssh json file id")
    bssh_output_file_id = get_bssh_json_file_id_from_analysis_output_list(bclconvert_output_data_list)

    # Read the json object
    bssh_json_dict = json.loads(
        read_icav2_file_contents_to_string(
            project_id=project_id,
            data_id=bssh_output_file_id
        )
    )

    # Now we have the bsshoutput.json, we can filter the output_data_list to just be those under 'output/'
    # We also collect the bcl convert output object to get relative files from this directory
    # Such as the IndexMetricsOut.bin file in the Reports Directory
    # Which we also copy over to the interops directory
    bcl_convert_output_path = Path(bclconvert_output_folder_obj.data.details.path) / "output"
    bcl_convert_output_fol_id = get_project_data_folder_id_from_project_id_and_path(
        project_id,
        bcl_convert_output_path,
        create_folder_if_not_found=False
    )
    bcl_convert_output_obj = get_project_data_obj_by_id(
        project_id=project_id,
        data_id=bcl_convert_output_fol_id
    )
    bclconvert_output_data_list = list(
        filter(
            lambda data_obj:
                (
                    # File is inside 'output' directory
                    data_obj.data.details.path.startswith(
                        str(bcl_convert_output_path) + "/"
                    ) and not (
                        # File is not the fastq_list_s3.csv or TSO500L_fastq_list_s3.csv
                        # This file is just a list of presigned urls that will expire in a week
                        data_obj.data.details.name.endswith("fastq_list_s3.csv")
                    )
                ),
            bclconvert_output_data_list
        )
    )

    # Get the basespace run id from the bssh output dict
    logger.info("Collecting basespace run id")
    basespace_run_id = get_basespace_run_id_from_bssh_json_output(bssh_json_dict)

    # Get run info (to collect the run id)
    logger.info("Collecting the run info xml file")
    run_info_file_id = get_run_info_xml_file_id_analysis_output_list(
        bclconvert_output_data_list
    )

    # Read in the run info xml
    run_info_dict = parse_runinfo_xml(
        read_icav2_file_contents_to_string(
            project_id=project_id,
            data_id=run_info_file_id
        )
    )

    # Collect the run id from the run info xml
    logger.info("Collecting the run id from the run info xml file")
    run_id = get_run_id_from_run_info_xml_dict(run_info_dict)

    # Get the samplesheet id
    # The samplesheet needs to be placed in every cttso directory
    # FIXME - to remove - don't need the samplesheet anymore
    # Since we're not copying over cttso runs
    # logger.info("Getting the samplesheet")
    samplesheet_path = get_samplesheet_path_from_analysis_output_list(
        bclconvert_output_data_list
    )
    samplesheet_file_id = get_samplesheet_file_id_from_analysis_output_list(
        bclconvert_output_data_list
    )

    #
    logger.info("Reading in the samplesheet")
    samplesheet_dict = read_v2_samplesheet(
        project_id=project_id,
        data_id=samplesheet_file_id
    )
    # Get fastq list csv
    logger.info("Getting the fastq list csv file")
    fastq_list_csv_file_id = get_fastq_list_csv_file_id_from_analysis_output_list(bclconvert_output_data_list)
    fastq_list_csv_pd = pd.read_csv(
        StringIO(
            read_icav2_file_contents_to_string(
                project_id=project_id,
                data_id=fastq_list_csv_file_id
            )
        )
    )

    # Merge the fastq list csv and the bssh output generation to collect the fastq paths
    # Return value is a dictionary where each key is a sample ID, and the list are the absolute fastq paths
    fastq_list_rows_df: pd.DataFrame = get_fastq_list_paths_from_bssh_output_and_fastq_list_csv(
        fastq_list_pd=fastq_list_csv_pd,
        bssh_output_dict=bssh_json_dict,
        project_id=project_id,
        run_output_path=Path(bclconvert_output_folder_obj.data.details.path)
    )

    # Get fastq list paths by sample id
    fastq_list_paths_by_sample_id = {}
    for sample_id, sample_df in fastq_list_rows_df.groupby("RGSM"):
        fastq_list_paths_by_sample_id.update(
            {
                sample_id: sample_df["Read1FileURISrc"].tolist() + sample_df["Read2FileURISrc"].tolist()
            }
        )

    # Generate the manifest output for all files in the output directory
    # to link to the standard output path from the run id
    logger.info("Generating the run manifest file")
    # <bclconvert_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id>
    dest_folder_path = generate_bclconvert_output_folder_path(
        run_id=run_id,
        basespace_run_id=basespace_run_id,
        portal_run_id=portal_run_id
    )
    dest_project_id = get_dest_project_id_from_ssm_parameter()
    run_root_uri = convert_project_id_and_data_path_to_icav2_uri(
            project_id,
            bcl_convert_output_path,
            DataType.FOLDER
    )
    run_manifest: Dict = generate_run_manifest(
        root_run_uri=run_root_uri,
        project_data_list=bclconvert_output_data_list,
        output_project_id=dest_project_id,
        output_folder_path=dest_folder_path
    )

    for read_num in [1, 2]:
        fastq_list_rows_df[f"Read{read_num}FileURIDest"] = fastq_list_rows_df[f"Read{read_num}FileURISrc"].apply(
            lambda src_uri: get_dest_uri_from_src_uri(
                src_uri,
                bcl_convert_output_path,
                dest_project_id,
                dest_folder_path
            ) + Path(urlparse(src_uri).path).name
        )

    # FIXME - to delete we don't copy over cttso runs anymore, part of the cttso v2 step functions now
    # # Query the samples from the bssh sample outputs to determine if there are any samples that need to be added
    # # to the cttso run cache path
    # cttso_run_configurations = []
    # logger.info("Checking for cttso samples - these need to be copied over twice!")
    # if "TSO500L_Settings" in samplesheet_dict.keys():
    #     # Iterate over each library id and add dest uri to the run manifest for each fastq
    #     cttso_library_ids = list(
    #         map(
    #             lambda tsodata_iter: tsodata_iter.get("Sample_ID", None),
    #             samplesheet_dict.get("TSO500L_Data", [])
    #         )
    #     )
    #
    #     # Get library ids
    #     for cttso_library_id in cttso_library_ids:
    #         # Add samplesheet to top level of library run directory
    #         # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> /
    #         # <library_id> + "_run_cache"
    #         run_folder_uri = convert_project_data_obj_to_icav2_uri(
    #             dest_project_id,
    #             get_cttso_library_run_path(
    #                 run_id=run_id,
    #                 basespace_run_id=basespace_run_id,
    #                 library_id=cttso_library_id,
    #                 portal_run_id=portal_run_id
    #             )
    #         ) + "/"
    #         samplesheet_dest_uri = run_folder_uri
    #
    #         # Add to manifest list
    #         run_manifest[samplesheet_as_uri].append(
    #             samplesheet_dest_uri
    #         )
    #
    #         # Append the run configuration containing the samplesheet
    #         cttso_run_configurations.append(
    #             {
    #                 "samplesheet_uri": samplesheet_dest_uri + "SampleSheet.csv",
    #                 "run_folder_uri": run_folder_uri
    #             }
    #         )
    #
    #         # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> /
    #         # <library_id> + "_run_cache" / <library_id>
    #         for fastq_uri in fastq_list_paths_by_sample_id.get(cttso_library_id):
    #             # Add fastq uri to list
    #             run_manifest[fastq_uri].append(
    #                 convert_project_data_obj_to_icav2_uri(
    #                     dest_project_id,
    #                     get_cttso_fastq_cache_path(
    #                         run_id=run_id,
    #                         basespace_run_id=basespace_run_id,
    #                         library_id=cttso_library_id,
    #                         portal_run_id=portal_run_id
    #                     )
    #                 ) + "/"
    #             )

    # Sanitise the manifest file - make sure theres no Path objects in there
    run_manifest = dict(
        map(
            lambda kv: (kv[0], list(map(str, kv[1]))),
            run_manifest.items()
        )
    )

    # Get the fastq list rows data frame
    fastq_list_rows_df = (
        fastq_list_rows_df.rename(
            columns={
                "Read1FileURIDest": "Read1FileURI",
                "Read2FileURIDest": "Read2FileURI",
            }
        ).drop(
            columns=[
                "Read1File",
                "Read2File",
                "Read1FileURISrc",
                "Read2FileURISrc",
                "sample_prefix"
            ]
        )
    )

    # Write out as a dictionary
    fastq_list_rows_df_list = fastq_list_rows_df.to_dict(orient='records')

    # Convert interop files to uris and add to the run manifest
    interops_as_uri = dict(
        map(
            lambda interop_iter: (
                convert_project_id_and_data_path_to_icav2_uri(
                        project_id,
                        Path(interop_iter.data.details.path),
                        data_type=DataType.FILE
                ),
                [
                    convert_project_id_and_data_path_to_icav2_uri(
                            dest_project_id,
                            (
                                dest_folder_path /
                                Path(interop_iter.data.details.path).parent.relative_to(
                                    input_run_folder_obj.data.details.path
                                )
                            ),
                            data_type=DataType.FOLDER
                    )
                ]
            ),
            interop_files
        )
    )

    # Add interops to the run manifest
    run_manifest.update(
        interops_as_uri
    )

    # Check IndexMetricsOut.bin exists in the Interop files
    # Otherwise copy across from Reports output from BCLConvert
    try:
        _ = next(
            filter(
                lambda interop_uri_iter: Path(urlparse(interop_uri_iter).path).name == 'IndexMetricsOut.bin',
                interops_as_uri.keys()
            )
        )
    except StopIteration:
        # Add 'IndexMetricsOut.bin' from reports directory to the interop files
        index_metrics_uri = convert_project_id_and_data_path_to_icav2_uri(
            project_id,
            Path(bcl_convert_output_obj.data.details.path) / "Reports" / "IndexMetricsOut.bin",
            data_type=DataType.FILE
        )

        # Append InterOp directory to list of outputs for IndexMetricsOut.bin
        run_manifest[index_metrics_uri].append(
            convert_project_id_and_data_path_to_icav2_uri(
                dest_project_id,
                dest_folder_path / "InterOp",
                data_type=DataType.FOLDER
            )
        )

    return {
        "manifest": run_manifest,
        "run_id": run_id,
        "basespace_run_id": basespace_run_id,
        "output_uri": convert_project_id_and_data_path_to_icav2_uri(
            dest_project_id,
            dest_folder_path,
            data_type=DataType.FOLDER
        ),
        "fastq_list_rows": fastq_list_rows_df_list,
        "samplesheet_dict": samplesheet_dict
    }


#
with open("test.json", "w") as f:
    f.write(json.dumps(
        handler(
            {
                "project_id": "b23fb516-d852-4985-adcc-831c12e8cd22",
                "analysis_id": "456cda16-ffad-452b-8b46-a0321ea434d1",
                "portal_run_id": "20240207abcduuid"
            },
            None
        ),
        indent=4
    )
)

