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
import logging

# Wrapica imports
from wrapica.enums import DataType
from wrapica.libica_models import ProjectData
from wrapica.project_data import (
    get_project_data_obj_by_id,
    read_icav2_file_contents_to_string,
    get_project_data_folder_id_from_project_id_and_path,
    convert_project_id_and_data_path_to_uri,
    convert_uri_to_project_data_obj
)
from wrapica.storage_configuration import convert_icav2_uri_to_s3_uri

# Local imports
from bssh_manager_tools.utils.manifest_helper import generate_run_manifest, get_dest_uri_from_src_uri
from bssh_manager_tools.utils.sample_helper import get_fastq_list_paths_from_bssh_output_and_fastq_list_csv
from bssh_manager_tools.utils.aws_ssm_helpers import set_icav2_env_vars
from bssh_manager_tools.utils.icav2_analysis_helpers import (
    get_bssh_json_file_id_from_analysis_output_list,
    get_fastq_list_csv_file_id_from_analysis_output_list, get_run_folder_obj_from_analysis_id,
    get_interop_files_from_run_folder, get_bclconvert_outputs_from_analysis_id,
)
from bssh_manager_tools.utils.compression_helpers import compress_dict
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
    dest_project_data_obj = convert_uri_to_project_data_obj(
        output_uri,
        create_data_if_not_found=True
    )

    dest_project_id = dest_project_data_obj.project_id
    dest_folder_path = Path(dest_project_data_obj.data.details.path)

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
                    ) and
                    not (
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
    run_root_uri = convert_project_id_and_data_path_to_uri(
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
            lambda src_uri: convert_icav2_uri_to_s3_uri(
                get_dest_uri_from_src_uri(
                    src_uri,
                    bcl_convert_output_path,
                    dest_project_id,
                    dest_folder_path
                ) + Path(urlparse(src_uri).path).name
            )
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
                convert_project_id_and_data_path_to_uri(
                    project_id,
                    Path(interop_iter.data.details.path),
                    data_type=DataType.FILE
                ),
                [
                    convert_project_id_and_data_path_to_uri(
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
        index_metrics_uri = convert_project_id_and_data_path_to_uri(
            project_id,
            Path(bcl_convert_output_obj.data.details.path) / "Reports" / "IndexMetricsOut.bin",
            data_type=DataType.FILE
        )

        # Append InterOp directory to list of outputs for IndexMetricsOut.bin
        run_manifest[index_metrics_uri].append(
            convert_project_id_and_data_path_to_uri(
                dest_project_id,
                dest_folder_path / "InterOp",
                data_type=DataType.FOLDER
            )
        )

    logger.info("Outputting the manifest and fastq list rows")

    return {
        "manifest_b64gz": compress_dict(run_manifest),
        "fastq_list_rows_b64gz": compress_dict(fastq_list_rows_df_list),
    }


# if __name__ == "__main__":
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "project_id": "a7c67a80-c8f2-4348-adec-3a5a073d1d55",
#                     "output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary_data/240229_7001234_1234_AHJLJLDS/20240530abcd1234/",
#                     "analysis_id": "47936e52-21fd-457b-a1dc-97139d571441"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "manifest_b64gz": "H4sIAIbSsGYC/+2dX0/jRhTFvwriuY7Hd8b/9g0ClKxALHhXW6mqRoM9BKuO7doOhVb97p1kl9ldsQtJNaSTyX0hB0Uid34+OXN9mSh/75e5uIM3vi/iPIpFQrw8uQGPUZZ4opC5R0UoSEyLoAhDv6xmtSdqUT30sveBEYCUHxASUMIJJAk/PA1Pz+Eo+2XMqYhELniexIJK7zCvxk19J7th745x4LFHgYV5GkWeyCnxWJErFVwHXpgEkkIcM1aEfjMf2vngnzXT3j/uuqbrR1Uz3X+z96suXIogFfQm9GQe5x5LGfEEi5mX0yAv0qC4FgXz266cie6BF2IQj3XHqm6gjC9/HJy+PXt7dpT5QNTTISXiOi8Wz3x67f3fftrbIlQfRVeX9RRhrQLrRPTDH+Nm1lZykKPhfkBiLxCb1DcNWut5UFeybbqh94/kbF4NpTLXPc8GMfSjvL/bKLjHSraP3UEh2kF2/FwOXZkjudXJTepC+e20aVu1DfBxM6/ReP/BeOOHvJJov7X53Sy2VF6V/YDQVoZ2Na+XG+v9rEJiKxHLxKJpy26lRJ+tTu1yLqpyeMBYW5vc+6blH+rf6+bPmh+KLm8KifjWbEo+u+5iPoyuyxrJrX0T8b5ULQneSawHsFs+jm4H3FvX3CWWdsOtYlV8n1qS3j8TteSBf6ZemQQEtOBZwM+U4lcBVw+jZac8mv61Uaw/KtJFzICYDWOOiBY8o5a6WRXpImZAzKYxgxY8C23FvP2hEWnBs8TW0IicxAyI2TDmMNWCZ2Cpm1WRLmZzgNlsGvMXwTNmK+bAScyAmDeRzYDZbAzzh7qQg+xmZS2Lb37hGbEuPL4p1mXkgMhfI7OpFjyLbN0aqZOYATEbwvzYRqexFjwLlhNSsMfOX1XpJGdAzqZjg2nBs9jWdGZOYgbEbDo1Qi14ltoazuHWY460UOFMbOUcOWlnQDtvxM6AdjbLGWiiheJM7YyNRZVOcgbkbIzzS8Mkq2ztwjBJmybVQlmb2RohqdPWBrT2xqwNaG3TnAMtFGewNUICNzkDcjbEmf54Ukrt8TPd+knp85wBORvODUa0UJxDS/OZka3385Phko2xEbppZ0A7m7bz0yGejX6OnIwNwNgwi/l7Mzz77LzFM7znYwMwNjbiZ0A/G+P80uDOqvhwYXC3EnJA5K+RJk9npTbujqmbnAE5G+L8eCosDbRQnJfnw5g9fv6qSic5A3I2nRtPZ/825vO2+xlYoIXinNqZG4sqneQMyNk0Zz2PBJ4BsdXP4CZnQM6mOadaKM6BrX5O3eQMyNkw55BooTiDpX4OiZv9M2D/vBE/A/rZNOdAC8WZ2pobgZucATmb5gxaKM7MVj+Dm5wBOZvmTLVQnENb/Uzd5AzI2XD//J1DdxbOn9n293VfhPJzZGtuMDf9DOhn034OtVB+jm31c+hmbgDmhmnOsRaKs63/HwxjNzkDct5IPgPms2nOkRaKc2JrbkRucgbkbPjcVxRqofpnS+9TFlU6yRmQs+lzjE8/i2zjedHYTc6AnI1xfukjFFbZ2oWPUKyEHBD5a6RJooVKk8TW1E7c5AzOcO7mde9f9/0tF20PXn/rtV1TcEZU4WngT2r1hrlo/YOqnNYzWQ//4/cFP9byuis9FL3MRVWV9dT5tR53XdO5v8r7QarkLxZfnev8Yi/aQf3t6rwpZOX+lZ21ZbdY7rtb0e/CG/by8woPHxbx7+4635383JWF85dz3HSdzAdZTHZgY92J+J3MxFTuTAwBocTdVZ58PD3fiRi63IUWsBP5UDa180vN5rNFgVdz95d6Jadlry7sTlzX47tduPueqBu1eytW+c+/Sza1iIyZAAA=",  # pragma: allowlist secret
#     #     "fastq_list_rows_b64gz": "H4sIAIbSsGYC/9WbW2/bRhCF/4qh55gi98JL3rYbdNtAfQm3T0VBMJJSGEiK1AkKtEX/e2coZeOGR2tIT7OAbQ1Iwz6YDzM7Z7n85Z/Nm/Djq83Lu01wLkYfYhWji8FR0Gxe3NHt8Se+vVOmrptana7tvvv22m7+/UjXGr59nA/N9w/vjz8/PvCvPeznP9XL7fY4N8Os39n7477b35vB1Pez6cz9Xjf7w9Ac3s4Hs/34+PBhfvxrOsyf5y39faWGqaP/orSZlh/uh9e717tX41bVdNvqen67P/Cd7Th/+Pj++GnLUqZm+0VdCqaxmXYUTW+aiT6qd/Onz39Uv/29OWtWojWr/2v+98XdU3ZML4TI9IKnLx8c4meHNb/TNan87JCCaVRl8IOac/wIXwjeOe8r712kr+gC4tfWa36na1L5tXUKplGXwQ9qzvF7Au0JSsSvAfwa0fy+BtNoCuGHNOf7Z2Rq3DQDswzUQXH9gfWvFb3+tSoF02gL4Yc0Z/vnsvYF5yPVH30sMCE/Dfhp0fx0CqaxLYQf0pzjRxMnV5yPvP5Fap6MEPIzgJ8Rzc+kYBq7QvghzVl+kahR33Se3QOxuzi/tIBfK5pfm4Jp7AvhhzQ/0z9PLdOzCaT6q9Sa3WDX7E7XzuyUFHZflo/BpmAaB86DEssuqznLjhsmDTDUOamFsgVE7EDdDa1odm0KyAPXhcCDorOTZyRmLix9My6uAdHrAL1ONL0uBZSIphB6UHR23fOBFroY2LXTp0e1p/Ta852vCaVH6lJAiVBF0LsgOlt7XHhEjTyf4yr0kF4P6PWi6fUpoEToQuhB0c95PrbqFa151Dcjrr0B0BtE0xtSQIkwhdCDorO1x5Mm/ahozaOZBa579L2mZ2rJ9EydAkqELYMeFn2dX9A3+AUthZ6+OHtrsfCymq/zC/oGvyCP3Xr0LgAeFH2dX9A3+AV59NajdwH0oOjr/IK+wS9Io4dGb/H0Loi+zi/oG/yCPHrr0bsAelD0dX5B3+AX5NFbj94F0IOir/ML+ga/II4eGL3l08Oi8zNn4IrjYfOMj8aXyoDnQ8AztE89g5FCMD0isymgZCwPO41YgnnRz9Tfacnj57SOA0BvAKdbhkYyvaFJASWiK4MeFn2dazA3uAZ59NYDeAH0oOjs6bLIx1vIsXMBcgzp9YBeL5penwJKRF8IPSg6X3uR3V5k17CcsQb0lAGez0junKQuBZSIoQh6F0TnJ5el4nyVtjwRPQXoKdH00t6vmkZVF0IPis6fq478ToNbTpV53vRE9IDnM4NoekMKKBFNIfSg6PypXK4+T50z+uV4IKJngeeztWR6tk4BJUKVQQ+LzjsG7897nYt5h7VnwbpnRa97tkkBJUIXQg+Kzu5UL6eoPT8lWvasA6QH1j0ret2zKgWUCFMIPSg66xj4dRQiR1MLv9ngHaSnAT0tmp5OASXCFkIPis77PTbr0VVsHZYntIieAfSMaHpfA0pEWwg9KPqZd4moZVLDdFx4hA/Ss4CeFU3PpoAS0RVCD4rOOgZ+98Tz1LI8LLqw7rWAXiuaXpsCSkRfCD0oOr/XEpbnC1Vchk/s92wH6HWi6XUpoEQUsteCRX9L79f/ABq6wvWCQAAA"  # pragma: allowlist secret
#     # }