#!/usr/bin/env python3

"""
Handle the workflow session object

The BCLConversion complete object looks something like this:

{
  "project_id": "a1234567-1234-1234-1234-1234567890ab",
  "analysis_id": "b1234567-1234-1234-1234-1234567890ab",
  "portal_run_id": "20240207abcduuid"
}

While the outputs will look something like this:

{
    "run_id": "231116_A01052_0172_BHVLM5DSX7",
    "basespace_run_id": 3659658,
    "output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3659658/20240207abcduuid/",
    "fastq_list_rows_b64gz": "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",
    "samplesheet_dict_b64gz": "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",
    "manifest_b64gz": "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"
}

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
    convert_project_id_and_data_path_to_icav2_uri
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
    get_samplesheet_file_id_from_analysis_output_list
)
from bssh_manager_tools.utils.compression_helpers import compress_dict
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
    logger.info("Collecting the analysis id and project context")
    project_id = event['project_id']
    analysis_id = event['analysis_id']

    logger.info("Collect the portal run id to configure the outputs")
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
    samplesheet_file_id = get_samplesheet_file_id_from_analysis_output_list(
        bclconvert_output_data_list
    )

    # We read in the samplesheet and return it as an output
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
                # "Read1FileURISrc",
                # "Read2FileURISrc",
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
        "run_id": run_id,
        "basespace_run_id": basespace_run_id,
        "output_uri": convert_project_id_and_data_path_to_icav2_uri(
            dest_project_id,
            dest_folder_path,
            data_type=DataType.FOLDER
        ),
        "fastq_list_rows_b64gz": compress_dict(fastq_list_rows_df_list),
        "samplesheet_dict_b64gz": compress_dict(samplesheet_dict),
        "manifest_b64gz": compress_dict(run_manifest)
    }


# if __name__ == "__main__":
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "project_id": "b23fb516-d852-4985-adcc-831c12e8cd22",
#                     "analysis_id": "456cda16-ffad-452b-8b46-a0321ea434d1",
#                     "portal_run_id": "20240207abcduuid"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "run_id": "231116_A01052_0172_BHVLM5DSX7",
#     #     "basespace_run_id": 3659658,
#     #     "output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3659658/20240207abcduuid/",
#     #     "fastq_list_rows_b64gz": "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",
#     #     "samplesheet_dict_b64gz": "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",
#     #     "manifest_b64gz": "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"
#     # }
