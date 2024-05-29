#!/usr/bin/env python3

"""
Handle the workflow session object

The BCLConversion complete object looks something like this:

{
  "project_id": "a1234567-1234-1234-1234-1234567890ab",  // The output project id
  "analysis_id": "b1234567-1234-1234-1234-1234567890ab", // The analysis id
  "instrument_run_id": "231116_A01052_0172_BHVLM5DSX7",    // The instrument run id
  "output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/231116_A01052_0172_BHVLM5DSX7/abcd1234/"  // A prefix to where the output should be stored
}

While the outputs will look something like this:

{
    "instrument_run_id": "231116_A01052_0172_BHVLM5DSX7",
    "output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/231116_A01052_0172_BHVLM5DSX7/20240207abcduuid/",
    "fastq_list_rows_b64gz": "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",  // pragma: allowlist secret
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
    generate_bclconvert_output_folder_path
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

    logger.info("Collect the output uri prefix")
    output_uri = event['output_uri']
    dest_project_id = urlparse(output_uri).netloc
    dest_folder_path = Path(urlparse(output_uri).path)

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
                sample_id: sample_df["Read1FileUriSrc"].tolist() + sample_df["Read2FileUriSrc"].tolist()
            }
        )

    # Generate the manifest output for all files in the output directory
    # to link to the standard output path from the run id
    logger.info("Generating the run manifest file")
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
        fastq_list_rows_df[f"Read{read_num}FileUriDest"] = fastq_list_rows_df[f"Read{read_num}FileUriSrc"].apply(
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
                "Read1FileUriDest": "Read1FileUri",
                "Read2FileUriDest": "Read2FileUri",
            }
        ).drop(
            columns=[
                "Read1File",
                "Read2File",
                "Read1FileUriSrc",
                "Read2FileUriSrc",
                "sample_prefix"
            ]
        )
    )

    # fastq list rows RGSM should also be the RGLB
    fastq_list_rows_df["RGLB"] = fastq_list_rows_df["RGSM"]

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
        "fastq_list_rows": fastq_list_rows_df_list,
    }


# if __name__ == "__main__":
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "project_id": "b23fb516-d852-4985-adcc-831c12e8cd22",
#                     "analysis_id": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
#                     "instrument_run_id": "240229_A00130_0288_BH5HM2DSXC",
#                     "output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "fastq_list_rows": [
#     #         {
#     #             "RGID": "GAATTCGT.TTATGAGT.1",
#     #             "RGSM": "L2400102",
#     #             "RGLB": "L2400102",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GAGAATGGTT.TTGCTGCCGA.1",
#     #             "RGSM": "L2400159",
#     #             "RGLB": "L2400159",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "AGAGGCAACC.CCATCATTAG.1",
#     #             "RGSM": "L2400160",
#     #             "RGLB": "L2400160",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "CCATCATTAG.AGAGGCAACC.1",
#     #             "RGSM": "L2400161",
#     #             "RGLB": "L2400161",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GATAGGCCGA.GCCATGTGCG.1",
#     #             "RGSM": "L2400162",
#     #             "RGLB": "L2400162",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ATGGTTGACT.AGGACAGGCC.1",
#     #             "RGSM": "L2400163",
#     #             "RGLB": "L2400163",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "TATTGCGCTC.CCTAACACAG.1",
#     #             "RGSM": "L2400164",
#     #             "RGLB": "L2400164",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "TTCTACATAC.TTACAGTTAG.1",
#     #             "RGSM": "L2400166",
#     #             "RGLB": "L2400166",
#     #             "Lane": 1,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ATGAGGCC.CAATTAAC.2",
#     #             "RGSM": "L2400195",
#     #             "RGLB": "L2400195",
#     #             "Lane": 2,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ACTAAGAT.CCGCGGTT.2",
#     #             "RGSM": "L2400196",
#     #             "RGLB": "L2400196",
#     #             "Lane": 2,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GTCGGAGC.TTATAACC.2",
#     #             "RGSM": "L2400197",
#     #             "RGLB": "L2400197",
#     #             "Lane": 2,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "TCGTAGTG.CCAAGTCT.2",
#     #             "RGSM": "L2400231",
#     #             "RGLB": "L2400231",
#     #             "Lane": 2,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GGAGCGTC.GCACGGAC.2",
#     #             "RGSM": "L2400238",
#     #             "RGLB": "L2400238",
#     #             "Lane": 2,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ATGGCATG.GGTACCTT.2",
#     #             "RGSM": "L2400239",
#     #             "RGLB": "L2400239",
#     #             "Lane": 2,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GCAATGCA.AACGTTCC.2",
#     #             "RGSM": "L2400240",
#     #             "RGLB": "L2400240",
#     #             "Lane": 2,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ATGAGGCC.CAATTAAC.3",
#     #             "RGSM": "L2400195",
#     #             "RGLB": "L2400195",
#     #             "Lane": 3,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ACTAAGAT.CCGCGGTT.3",
#     #             "RGSM": "L2400196",
#     #             "RGLB": "L2400196",
#     #             "Lane": 3,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GTCGGAGC.TTATAACC.3",
#     #             "RGSM": "L2400197",
#     #             "RGLB": "L2400197",
#     #             "Lane": 3,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "TCGTAGTG.CCAAGTCT.3",
#     #             "RGSM": "L2400231",
#     #             "RGLB": "L2400231",
#     #             "Lane": 3,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GGAGCGTC.GCACGGAC.3",
#     #             "RGSM": "L2400238",
#     #             "RGLB": "L2400238",
#     #             "Lane": 3,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ATGGCATG.GGTACCTT.3",
#     #             "RGSM": "L2400239",
#     #             "RGLB": "L2400239",
#     #             "Lane": 3,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GCAATGCA.AACGTTCC.3",
#     #             "RGSM": "L2400240",
#     #             "RGLB": "L2400240",
#     #             "Lane": 3,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ACGCCTTGTT.ACGTTCCTTA.4",
#     #             "RGSM": "L2400165",
#     #             "RGLB": "L2400165",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GCACGGAC.TGCGAGAC.4",
#     #             "RGSM": "L2400191",
#     #             "RGLB": "L2400191",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GTCGGAGC.TTATAACC.4",
#     #             "RGSM": "L2400197",
#     #             "RGLB": "L2400197",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "CTTGGTAT.GGACTTGG.4",
#     #             "RGSM": "L2400198",
#     #             "RGLB": "L2400198",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GTTCCAAT.GCAGAATT.4",
#     #             "RGSM": "L2400241",
#     #             "RGLB": "L2400241",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "ACCTTGGC.ATGAGGCC.4",
#     #             "RGSM": "L2400242",
#     #             "RGLB": "L2400242",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "AGTTTCGA.CCTACGAT.4",
#     #             "RGSM": "L2400249",
#     #             "RGLB": "L2400249",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GAACCTCT.GTCTGCGC.4",
#     #             "RGSM": "L2400250",
#     #             "RGLB": "L2400250",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GCCCAGTG.CCGCAATT.4",
#     #             "RGSM": "L2400251",
#     #             "RGLB": "L2400251",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "TGACAGCT.CCCGTAGG.4",
#     #             "RGSM": "L2400252",
#     #             "RGLB": "L2400252",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "CATCACCC.ATATAGCA.4",
#     #             "RGSM": "L2400253",
#     #             "RGLB": "L2400253",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "CTGGAGTA.GTTCGGTT.4",
#     #             "RGSM": "L2400254",
#     #             "RGLB": "L2400254",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GATCCGGG.AAGCAGGT.4",
#     #             "RGSM": "L2400255",
#     #             "RGLB": "L2400255",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "AACACCTG.CGCATGGG.4",
#     #             "RGSM": "L2400256",
#     #             "RGLB": "L2400256",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#     #         },
#     #         {
#     #             "RGID": "GTGACGTT.TCCCAGAT.4",
#     #             "RGSM": "L2400257",
#     #             "RGLB": "L2400257",
#     #             "Lane": 4,
#     #             "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#     #             "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#     #         }
#     #     ]
#     # }
