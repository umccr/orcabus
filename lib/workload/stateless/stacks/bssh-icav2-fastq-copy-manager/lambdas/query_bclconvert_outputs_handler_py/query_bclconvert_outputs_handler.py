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
        "manifest_b64gz": compress_dict(run_manifest),
        "fastq_list_rows_b64gz": compress_dict(fastq_list_rows_df_list),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            handler(
                {
                    "project_id": "b23fb516-d852-4985-adcc-831c12e8cd22",
                    "analysis_id": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
                    "output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/"
                },
                None
            ),
            indent=4
        )
    )

    # {
    #     "manifest_b64gz": "H4sIAH+KVmYC/+2dX2/bNhTFv0qQ58kSr0T96VviJouBBGmjFh0wDAQt0Y4wWdIkOYs77LuPdhu2RdrELhiPou9D4hPkwZc/H55LXcvwP8dFxu/gletOwZ9NKQmdPKbgBElMHZ5nmRP7JCMg4iwHcItyUTm84uWqE50LgQeQsBPPI77HPIhjdnpBL67gdfrbmMVBkFDCgkyQBJzTrBzX1Z1o+6O7gAGLHAiiTEyzxJnybOoE3ix3OPEzh8pfs4j4wg+nbr3sm2XvXtbzzj1r27rtRmU9P3519LsqPKIJFfEMHB9y3wmyKHS4D4GThTymORdxNKWbwlnTFgverp6u2wVP/p9CnPPQCzxCPj358R+/HA2I1Tnv+r/G9aIpRS9G/X2PyJ5D9oG3VVHN0WDP0boRTd32nXuS86YXLbsSfVtk3Sjr7vbL7aGQ4aF7LRbLsi/k7rxnac97hLftLp1Usxp36JY2e7vkZdGvcIfuji7l696Z3grRI7btsU2qXEbaRd00spWycb2sMNt24XezrDYJd78oEdlux5DxKisFRt3uAGfrawVWFh0m3U8e4d4V0nl4jvuZXvF5v14v+9G0qBDdduje1Q17X/1Z1X9X7JS3WZ0LtN4O/NrN4+i2xza767XEJuuwy27N79OFROde8koweSUpn9kjHijBUsIupWI3hMmH0aYbj+Yf98v1R1XayBmQs27OoacES31T/SyrtJEzIGftnEEJllJjOQ8/N0IlWBobmxuhlZwBOe8lNwjmhm7ONFGCpWAqZ1nl0P38RbA0MDY3iJWcCXLeS24A5oY+zu+rXPSiXRSVyL/5g6Weeb7+plqbmQMyf5Hc9pVgaWhsbvtWcgbkrIvzw2VLEinBUrIZmIJBhv6qTCtBA4LWnhyBEiyNjE3owErOgJy1BwdVgqWJsQFNB885VEIGtGcs6NBKQwMaej+GBjS0ZtDgx0pI0L6hybEuc7Cgnxt4mMXbhoHH0+YGNLd20IkSEnRgbIokVqcIYIrsz9yA5tYOmighQYOxKULsBA0IWhdo/8eDU98gR/uDH5w+DRoQtHbQjwYgRhp66AMQ+aOENDQ1tRcGnp2gAUFrT47HIz0joyO0MqIBI1oz5+9Nlww09ICnS08nB2By7MfRgI7WB/q5MZ5ZCWLDGG8r5oDMXyRQHo9OjWyRiZ2gAUHrAv1ww1hClJCgN7eOBQY5+qsyrQQNCFp7dDx+M8DIjB66oyEgSkjQiaHRsS7TStCAoLWDVtNJYCl4xjoa7AQNCFo76EQJCZoY6+jETtCAoHWDpp4SEjSY6mjq2XmOBjxH78fRgI7WDpooIUH7xkYHsRM0IGjtoEEJCTow1tFgJ2hA0NpB+0pI0NRYR/t2ggYErfsc/Z0b8kycRwfDP959EdLRobHREQweNFVCgo6MBU3tjA7A6NhPdABGh3bQkRIStLHvGdLITtCAoPfTDAGboXbQoRISdGxsdIR2ggYErfuWsJAqIY93pl6wrMu0EjQgaO03OT7+2LKRd5NGdoIGBK0P9HOfsjDL2DZ8ymIr5oDMXyRQYiVkoMTGJndsJ2iwB3S7rDp32nW3jDcdON2t07R1zvw4loVQd1LJLXPduCdlMa8Wour/z+8gfijmZZd6yjuR8bIsqrn9iz1r27o9gGUumkIukZdvbnl3EC/suG5bkfUinxzCnj2774Vs7/n6C5ftX+1106+9fFXnorR/tZMFnx/Ai5ouF+vibpaV/Wt9c/5rW+QHEUstz/qiPoDX9O3nJZ6u1idTixd6GD3m/MPF1WFs0gfjgud7B7BMm+P27iAuUG/EvOhkYzmMvjKR5/p7M5b573/PZmjGApoAAA==",  #  pragma: allowlist secret
    #     "fastq_list_rows_b64gz": "H4sIAH+KVmYC/9Wb7WvcRhDG/xVzn2OdtC96ybfNhmwKzpdoC4FShGpfwoEdUqcU2tL/vTO6y8aNnltz92kWbN8gGfthfszsPKvVL/9s3oefXm9eXm2CczH6EKsYXQyOgmbz4opuj+/49o0ydd3U6nDt5tWP127mzzu61vDt3XzXvNnf735+3POv7W/nP9XL7bazg931H9W1Vnf62tx27fWslbm+befe3s27vvvNbvf3D5+nL4/7h/nxry39faWGydF/0fVUq76fXr21b9+p1+MHv1U13beqv5vb2tRNsx3nhy/3u69b1jI122/yUjCNzXRD0fS+meij+jh//eP36tPfm6NoJVu0+r/of19cPaXH/EKIzC94+vLBIYJ2WBM8XBNL0A4pmEZVCEEoOkeQAIbgnfO+8t5F+oouIIJtvSZ4uCaWYFunYBp1IQSh6BzBJ9iewEQEG0CwkU3wezCNphSCSHS+i0bmxq0zMM1AfRTXIFgHW9nrYKtSMI22FIJIdLaLLmtgcD5SDdLHghMS1ICglk1Qp2Aa21IIItE5gjR9ctX5yOtgpBbKECFBAwga2QRNCqaxK4UgEp0lGIkbdU/n2UsQvZOTTAsItrIJtimYxr4Ugkj0M1300Dg9m0KqwUqt6Q12Te9w7UhPiaH3bRUZbAqmceBEKLn0sqKz9Lht0ihD/ZMaKVtCRA/U3tDKptemgExxXQo+qDo7hUai5sLSPePiIRC/DvDrZPPrUkCZaErhB1Vn1z8faMGLgX08fXpUf0qvPeDxmlR+JC8FlAlVBr8TqrP1x8VH3MgDOq5ED/n1gF8vm1+fAsqELoUfVP2cB2TzXtHaR90z4vobAL9BNr8hBZQJUwo/qDpbfzx10o+K1j6aXuD6R99rfqYWzc/UKaBM2EL4YdXnuQd9gXvQYvjpk4O4losvK/o896AvcA8C6a3n8BLwQdXnuQd9gXsQyG89h5fAD6o+zz3oC9yDOH5oDpfP74Tq89yDvsA9COS3nsNL4AdVn+ce9AXuQSC/9RxeAj+o+jz3oC9wD/L4gTm8AH5YdX7+DFx1PHgeAdIgUxnw9Ag4iPapgzBiGKYnaDYFlI3laaiRyzCv+pkaPCx9/CTXcQD4DeAUzNCI5jc0KaBMdIXww6rP8xDmAg8hkN96Gi+BH1SdPYkW+RgMeXguQo4hvx7w62Xz61NAmehL4QdV5+svsvuL7CGWc9mAnzLAAxrR/ZPkpYAyMZTB74Tq/AyzVJ2v0lYo4qcAPyWbX9oUVtOo6lL4QdX5s9iR34Vwywk0z5uhiB/wgGaQzW9IAWWiKYUfVJ0/x8sV6Kl/Rr8cJkT8LPCAthbNz9YpoEyoQvhh1Xn/4P1xD3Sx87D+LFj/rOz1zzYpoEzoUvhB1dk97OXktednSMtudoD8wPpnZa9/VqWAMmFK4QdVZ/0Dv8hC7Gh+4TcivIP8NOCnZfPTKaBM2FL4QdV5/8f2PbqKjcTyDBfxM4Cfkc3ve0CZaEvhB1U/8x4SNU5qm46LjwBCfhbws7L52RRQJrpS+EHVWf/Ab614nl+WR0kn1r8W8Gtl82tTQJnoS+EHVef3X8Ly7KGKyyCK/Z/tAL9ONr8uBZSJUvZfsOof+f36H1n1Xz7MQAAA"  #  pragma: allowlist secret
    # }
