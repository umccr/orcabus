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
    convert_project_id_and_data_path_to_uri
)

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
#                     "analysis_id": "47936e52-21fd-457b-a1dc-97139d571441",
#                     "output_uri": "icav2://development/primary_data/240424_A01052_0193_BH7JMMDRX5/202406066dd81cc9/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "manifest_b64gz": "H4sIABfArGYC/+2db2/aSBDGv0qU12dsj//3XUKSC6egNrhVK51Oq429AeuM7bMNl9zpvvsttNm2StoEytJlNFIknigRnvn54dn1YMS/x0XGl/DKtnmUhRGPHSuLb8HyPT+2eC4yy+MBdyIvd/MgsItyXlm84uV9JzobfAcgYSeO43oOcyCO2ellcDmGs/TDkHk85BlnWRxxT1inWTmsq6Vo+6Olz4BFlgd+kCVhaPHMcyw/z6Ryb1wriF3hQRT5fh7Y9aJvFr19VU87+7xt67YblPX0+NXR78edJ6tuikaURSWsXCytjGczYQWOl0QRREHoymdsrE4+x0zwrrfAbtpiztt7lvOer8r3wZflu04AzHETT5Yf/TYen00+BDY48u+hE4Z5HrtZlnys4fiPX44OCNl73lZFNSVom0C7kG3/NaznTSl6MejveiL3QnKj6rYmq70M2EQ0ddt39pmYL8q+kGa7Y2nP+26QdcufAvChosNjeJLzphctG4u+LTIiuDnBUZVL/13WTSOXCzasFxUZ8QeMOLzPSkF23Jrj7WoJZmXR9QRvY3iTRbVeiO/mJZHbiFzKV5u+dCYE+W5zetcLXhb9PcXe1gTf1g17V/1Z1X9X7JS3WZ0LwrjlZuaTC18v+sFNURHBrS9K3hZyK0NXJtuBbNePg1lPa/GWq8nafrSkbIrx41ams694JZhrX8kjy15BCZa67EoqNnGZfBisd9yD6T8/Be+3isWIGwi3JtyhowRLPcPdLYvFiBsIty7coARLA9NxH36YhEqwNDY9TEKUuIFwa8IdJEqwFAx3tywWY3a7lN26cH8WLPVNx+2ixA2Ee5/ZDZTdO8f9rspFL9q5xJd/9QtLHWND5auiMaMHQq8z0z0lWBqavoR6KHED4d4x7odteBIpwVJ3PZkF8+z9RbUoeQPx1hUnvhIsjUxPbx8lbiDcutIkUIKlienhHRw87lAJGd6O6bxDlPYGsvde7Q1kbz28wYuVkLw9s+NkVS1K3kC8d877uaGVkTbHMLRS5kmUkFb3TY+WBLXVgay+d6sDWV0Xb1cJyRtMjxYXJ28g3jvm7X17QuuZ52/v4Ce03+cNxFtTnviOEpJ3YHh++87B+/vREMvkOAlw2hvI3rrs/XhoaLK/Q5RxAhQnenA/NTM0194HPDP8fpwAxcle/Q3k753zfm5QaGSsYBgUvgg9EHqdKfN4RmvyKprg5A3Ee8e8H+52S1wlJO/1fW++ef7+olqUvIF468qTx+9BmJzfh+5v8F0lJO/E7DxZVYuSNxBvXbzV/BNYCo7p/gacvIF46+KdKCF5u6b7O8HJG4i3Jt6Bo4TkDYb7O3Bw7r+B9t979TeQv3XxdpWQvD3T88TFyRuIty7eoITk7Zvub8DJG4i3Lt6eEpJ3YLq/PZy8gXhr2n8/cVOhwfNv//D3g5+F9Hdoep74OP0N5G9d/g6UkP6OTPd3gDNPgPJEF+9ICcnb9PcvgwgnbyDee81voPzWxTtUQvKOTc+TECdvIN6a7mcLAyXk/tvw651VtSh5A/HWdb/m4894m3x/bISTNxDvnfN+7qMlRtocw0dLXoQeCL3OlImVkCkTm57qMU7egI53u6g6+6brZow3HVjdzGraOme+k8gf1x5V8gX0urFPymJazUXVP/H91g8Hlb2Lsm5W//VDHT4cU29Hp7wTGS/lWZui6em8besWTzd3vZAJnq++ihlNU6+bXj53Oa5zUeI5U/OmaFdtvZnxDtML6vpTJ6f3q7g9/H7eXPzaFjma0zOs21ZkvchHiBYmVHE3mvOpQBcH4HjO4Xdz8f5yjCoOrjFtfVqe9UVdoWkpXcxXFU4WeFqaiGnRyROF6jydLzFd5Y3kBcTdXrv5738WyW3/3JoAAA==",  #  pragma: allowlist secret
#     #     "fastq_list_rows_b64gz": "H4sIABfArGYC/9Wbb2vjRhDGv0rw67Ms7T9Z925vj25bkjfRFgqlCBO7PUPumiZpoS397p2RfXvp6fEG+5UGkniQAn6YHzM7z2r10z+L2/jd+8Xbq0X0PqUQU5WST9FT0CzeXNHt/oZvXytT102tDteu33197XrzaUfXGr6922ybb/b3ux8e9/xvT/rtavWwf9jd7z/tltvdn8u7zd2H3dLWumtb1VrXuOXmYfn02x/PH3abp+elWj087j9uHv8atpvnzYq+xigzePouq4a66fTw7tv2+5ub97c/2pWq6b6rndtu183dXbfqNx8f7ndPK5Y0NKvPKnMw9M1wTdFw2wz0Uf1CX/l79evfi6N2JUK7+r/2f99cvWTJNGNMTDMG+gnRI562m/I8XJs7T9vlYOiVLJ5Qe4kn4YwxeB9CFYJP9JN8RDxdPeV5uDZ3nq7OwdBrWTyh9hLPFxBfoEU8G8CzEcHzSzD0RhhPpL3cbxNT5CYbmW2kjovrE6yfTsT66VQOht4K44m0F/vtuHZGHxLVJ32McCFPDXhqETx1DobeCeOJtJd40kTLFRkSr5+Jmi0jhTwN4GlE8DQ5GPpWGE+kvcgzEUXqsz6wWyGWJ+chB3g6ETxdDoZ+LYwn0v5Kvz202MAmlOqzUlOWnZ2yPFw7slRzY/l52elsDoa+43yo2bMsai+y5AZLAxF1Wmq5bEERS1CXnRPB0uWAvHgtDCYUX5xsEzH0ceyzaXQpiGYLaLYiaLY5oIQ0wmhC8cV1M0RaKFPkXQT6DKg2lZ56zuO1mdMklTmghChRNE+IL9YmFyZRJM/puUoDpLkGNNciaK5zQAnRwmhC8a95Tt46qGjNpD6bcG12gGYngmaXA0qIEUYTii/WJk+y9KeiNZNmILhu0u+Upqkl0DR1DighVhZNLP48f6Iv8Cd6bjT1yRlfzx5mUft5/kRf4E/my3I64guCCcWf50/0Bf5kvjSnI74gmlD8ef5EX+BP5koTjfhiaJ4Qf54/0Rf4k/nSnI74gmhC8ef5E32BP5kvzemIL4gmFH+eP9EX+JPZ0gQjvhyaWHx5po1ckTzMHnHSOFQZ8DwMeBT30qOYuRHNjwZtDigp40NfM3uiZfGv1OdhyeTn1p4DQLMDp4O6RgLNrskBJaSVRROLP8+lmAtcynxpTgd9QTSh+OLpvcTHg3yquEA5hjTXgOZaBM11Digha2E0ofhybSZ2m4ldyngGHtBUBnhOI6HTksocUEI6UTRPiC9PQmNFhipv2SKaCtBUImjmPWw19KoWRhOKL597T/xOih9P7QXetEU0gec0nQiaXQ4oIY0wmlB8+ZQ0V2egTpvCeBwT0bTAc9paAk1b54ASomTRxOLLDiWE417tuJkAa9OCddOKWDdtkwNKiBZGE4ov7ryPp9wDPxUb9+AjpAnWTSti3bQqB5QQI4wmFF90KPx6EZGkKYjfTAke0tSAphZBU+eAEmKF0YTiy36TNw+Sr9iqjE+sEU0DaBoRNL8ElBAnjCYU/8q7YtRiqcF6LkzCCWlaQNOKoGlzQAlphdGE4osOhd8lCjwFjQ/HTqybDtB0Imi6HFBC1sJoQvHlvaA4Pj+p0jjcYr9pW0CzFUGzzQElRNheEBb/Nc2f/wMHcuL20kIAAA=="   #  pragma: allowlist secret
#     # }
