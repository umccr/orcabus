#!/usr/bin/env python3

"""
Merge file sizes for fastq list rows

Given the output directory,
* collect the file sizes for the original gzipped tsv,
* the md5sum txts for both the fastq gzipped and ora files
* collect the file sizes for the new ora compressed tsv


"""
from io import StringIO

import pandas as pd
import typing
import boto3
from os import environ
from urllib.parse import urlparse, urlunparse
from pathlib import Path

# Wrapica imports
from wrapica.enums import DataType, UriType
from wrapica.project_data import (
    ProjectData,
    convert_uri_to_project_data_obj,
    list_project_data_non_recursively,
    read_icav2_file_contents, convert_project_data_obj_to_uri
)

# Type checking
if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


# AWS things
def get_ssm_client() -> 'SSMClient':
    """
    Return SSM client
    """
    return boto3.client("ssm")


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_ssm_parameter_value(parameter_path) -> str:
    """
    Get the ssm parameter value from the parameter path
    :param parameter_path:
    :return:
    """
    return get_ssm_client().get_parameter(Name=parameter_path)["Parameter"]["Value"]


def get_secret(secret_arn: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_arn)["SecretString"]


# Set the icav2 environment variables
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def read_md5sum(project_data: ProjectData) -> pd.DataFrame:
    """
    Read the csv from the icav2
    :param project_data:
    :return:
    """
    with StringIO(read_icav2_file_contents(project_data.project_id, project_data.data.id)) as file_contents:
        return pd.read_csv(
            file_contents,
            header=None,
            names=["md5sum", "fastqPath"],
            sep="  ",
            engine="python"
        )


def read_file_sizes(project_data: ProjectData) -> pd.DataFrame:
    with StringIO(read_icav2_file_contents(project_data.project_id, project_data.data.id)) as file_contents:
        return pd.read_csv(
            file_contents,
            sep="\t"
        )


def read_fastq_list_csv(project_data: ProjectData) -> pd.DataFrame:
    """
    Read the csv from the icav2
    :param project_data:
    :return:
    """
    with StringIO(read_icav2_file_contents(project_data.project_id, project_data.data.id)) as file_contents:
        return pd.read_csv(file_contents).rename(
            columns={
                "RGID": "rgid",
                "RGLB": "rglb",
                "RGSM": "rgsm",
                "Lane": "lane",
                "Read1File": "read1File",
                "Read2File": "read2File"
            }
        )


def get_icav2_file_from_folder(project_data_list: typing.List[ProjectData], file_name: str) -> ProjectData:
    """
    Get the file from the list
    :param project_data_list:
    :param file_name:
    :return:
    """
    try:
        return next(
            filter(
                lambda project_data_iter: (
                        project_data_iter.data.details.name == file_name and
                        DataType[project_data_iter.data.details.data_type] == DataType.FILE
                ),
                project_data_list
            )
        )
    except StopIteration:
        raise ValueError(f"{file_name} not found in the project data list")


def merge_fastq_list_rows_with_md5sums_and_filesizes(
        fastq_list_ora_df: pd.DataFrame,
        fastq_raw_md5_df: pd.DataFrame,
        fastq_ora_md5_df: pd.DataFrame,
        fastq_gzipped_filesizes_df: pd.DataFrame,
        fastq_ora_filesizes_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Given the fastq list rows, the md5sums and the file sizes, merge them together
    :param fastq_list_ora_df:
    :param fastq_raw_md5_df:
    :param fastq_ora_md5_df:
    :param fastq_gzipped_filesizes_df:
    :param fastq_ora_filesizes_df:
    :return:
    """
    # Extend the gzipped md5s to the fastq list rows
    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_raw_md5_df.assign(
            fastqPath=lambda row_iter_: row_iter_.fastqPath.str.rstrip(".gz") + ".ora"
        ),
        how="left",
        left_on="read1File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"md5sum": "read1FileRawMd5sum"}
    ).merge(
        fastq_raw_md5_df.assign(
            fastqPath=lambda row_iter_: row_iter_.fastqPath.str.rstrip(".gz") + ".ora"
        ),
        how="left",
        left_on="read2File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"md5sum": "read2FileRawMd5sum"}
    )

    # Extend the ora md5s to the fastq list rows
    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_ora_md5_df,
        how="left",
        left_on="read1File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"md5sum": "read1FileOraMd5sum"}
    ).merge(
        fastq_ora_md5_df,
        how="left",
        left_on="read2File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"md5sum": "read2FileOraMd5sum"}
    )

    # Extend the gzipped file sizes to the fastq list rows
    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_gzipped_filesizes_df.assign(
            fastqPath=lambda row_iter_: row_iter_.fastqPath.str.rstrip(".gz") + ".ora"
        ),
        how="left",
        left_on="read1File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"fileSizeInBytes": "read1GzippedFileSizeInBytes"}
    ).merge(
        fastq_gzipped_filesizes_df.assign(
            fastqPath=lambda row_iter_: row_iter_.fastqPath.str.rstrip(".gz") + ".ora"
        ),
        how="left",
        left_on="read2File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"fileSizeInBytes": "read2GzippedFileSizeInBytes"}
    )

    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_ora_filesizes_df,
        how="left",
        left_on="read1File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"fileSizeInBytes": "read1OraFileSizeInBytes"}
    ).merge(
        fastq_ora_filesizes_df,
        how="left",
        left_on="read2File",
        right_on="fastqPath"
    ).drop(
        columns='fastqPath'
    ).rename(
        columns={"fileSizeInBytes": "read2OraFileSizeInBytes"}
    )

    # Return the fastq files
    return fastq_list_ora_df


def join_url(base_url: str, path: str) -> str:
    """
    Join the base url and the path
    :param base_url:
    :param path:
    :return:
    """
    url_obj = urlparse(base_url)

    return str(urlunparse(
        (
            url_obj.scheme,
            url_obj.netloc,
            str(Path(url_obj.path).joinpath(path)),
            None, None, None
        )
    ))


def handler(event, context):
    """
    Given the output directory

    * collect the new fastq list rows csv file
    * collect the file sizes for the original gzipped tsv,
    * the md5sum txts for both the fastq gzipped and ora files
    * collect the file sizes for the new ora compressed tsv
    :param event:
    :param context:
    :return:
    """

    # Set the icav2 env vars before anything else
    set_icav2_env_vars()

    # Get the output directory
    output_dir_uri = event["output_dir_uri"]
    convert_to_icav2_uri = event.get("convert_to_icav2_uri", False)

    # Get the output directory as an icav2 object
    output_dir_project_obj: ProjectData = convert_uri_to_project_data_obj(output_dir_uri)

    # Analysis list
    output_dir_project_data_list = list_project_data_non_recursively(
        project_id=output_dir_project_obj.project_id,
        parent_folder_id=output_dir_project_obj.data.id,
    )

    # Get the new fastq list rows csv file
    fastq_list_ora_df = read_fastq_list_csv(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_list_ora.csv")
    )

    # Get the md5sum txts for both the fastq gzipped and ora files
    fastq_gzipped_md5_file_obj = read_md5sum(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_raw.md5.txt")
    )

    # Get the file sizes for the new ora compressed tsv
    fastq_ora_md5_file_obj = read_md5sum(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_ora.md5.txt")
    )

    # Get the original gzipped tsv file size
    fastq_gzipped_filesizes_file_obj = read_file_sizes(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_gzipped.filesizes.tsv"
        )
    )

    # Get the md5sum txts for both the fastq gzipped and ora files
    fastq_ora_filesizes_file_obj = read_file_sizes(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_ora.filesizes.tsv"
        )
    )

    # Merge the fastq list rows with the md5sums and file sizes
    fastq_list_ora_df = merge_fastq_list_rows_with_md5sums_and_filesizes(
        fastq_list_ora_df,
        fastq_gzipped_md5_file_obj,
        fastq_ora_md5_file_obj,
        fastq_gzipped_filesizes_file_obj,
        fastq_ora_filesizes_file_obj
    )

    if convert_to_icav2_uri:
        output_dir_uri = convert_project_data_obj_to_uri(
            output_dir_project_obj,
            uri_type=UriType.ICAV2
        )

    # Convert read1File and read2File to URIs
    fastq_list_ora_df["read1FileUri"] = fastq_list_ora_df["read1File"].apply(
        lambda file_name: join_url(output_dir_uri, file_name)
    )
    fastq_list_ora_df["read2FileUri"] = fastq_list_ora_df["read2File"].apply(
        lambda file_name: join_url(output_dir_uri, file_name)
    )

    # Delete read1File and read2File columns
    fastq_list_ora_df.drop(
        columns=["read1File", "read2File"],
        inplace=True
    )

    # FIXME Drop rgid and rglb since we don't
    # FIXME accurately have these values yet
    # FIXME this will be possible once the fastq manager exists
    fastq_list_ora_df.drop(
        columns=["rgid", "rglb"],
        inplace=True
    )

    # Return the merged file as a json list
    return fastq_list_ora_df.to_dict(orient="records")


# if __name__ == "__main__":
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "convert_to_icav2_uri": True,
#                     "output_dir_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
# # [
# #     {
# #         "rgsm": "L2401537",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "5923a6ae1351243c196a6526376ad689",# pragma: allowlist secret  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "d0587ebc6a83a14f791423bb198f4b6a",# pragma: allowlist secret  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "509e126e0bf734a3f65caf6c49eb3715",# pragma: allowlist secret  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "f0e5487d1be657d66997cf52369fb8cb",# pragma: allowlist secret  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 57604117,
# #         "read2GzippedFileSizeInBytes": 58247458,
# #         "read1OraFileSizeInBytes": 20303567,
# #         "read2OraFileSizeInBytes": 20866911,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401537/L2401537_S22_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401537/L2401537_S22_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401553",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "42e4871ba2afd7cc0ad3d7bcfc5c8259",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "8f5c4a1039a1c873878661846b1f61a3",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "f04679d570d4aa000b8d8c5adc4960b0",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "6f5e75572cc8cbe70c008dad92edd6e2",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 35683061339,
# #         "read2GzippedFileSizeInBytes": 38483719785,
# #         "read1OraFileSizeInBytes": 6617978068,
# #         "read2OraFileSizeInBytes": 8629405567,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401553/L2401553_S27_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401553/L2401553_S27_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401533",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "880b39c74e406ccfd44aec66d6d7fe57",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "64359aa03a7662fc12d3028de217e4a2",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "cdbc3e8778e078d20ba3a558dd8d3d71",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "d1fbad47b621f920f654626e97f02993",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 6179483185,
# #         "read2GzippedFileSizeInBytes": 6065388584,
# #         "read1OraFileSizeInBytes": 1209397423,
# #         "read2OraFileSizeInBytes": 1129072555,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401533/L2401533_S18_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401533/L2401533_S18_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401534",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "b0b32fe9482dcdb6710214f48a3179a1",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "2f81751a8df8413718e943be03843f4a",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "4ee4f545716b187a8af7b110e582f2ae",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "8f12ed32cc67ccb013807044a880b0ee",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 6628903368,
# #         "read2GzippedFileSizeInBytes": 6559410472,
# #         "read1OraFileSizeInBytes": 1299905533,
# #         "read2OraFileSizeInBytes": 1238284291,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401534/L2401534_S19_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401534/L2401534_S19_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401549",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "2ed16482feafd5ad3ff9dd3dd153aa26",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "6a97988a8faab94905d9693e38a7f50a",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "c5ff45a7fb9690f41f0d81c015288e89",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "cd8c4fe281b7ecbee45eb15e0376360c",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 86165891313,
# #         "read2GzippedFileSizeInBytes": 92043170392,
# #         "read1OraFileSizeInBytes": 15540038685,
# #         "read2OraFileSizeInBytes": 19403308615,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401549/L2401549_S25_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401549/L2401549_S25_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401552",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "1c529416ac85f8157beea3274dcfc1ac",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "e03ebe7fa52194351167efc70ab9daf8",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "58c8aa1f43a331b1d4885ed487e0c12d",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "0e836c2917f9d4379d9273b233feea4a",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 33237582408,
# #         "read2GzippedFileSizeInBytes": 36766116815,
# #         "read1OraFileSizeInBytes": 6123700775,
# #         "read2OraFileSizeInBytes": 8612068652,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401552/L2401552_S26_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401552/L2401552_S26_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401536",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "83f07c1ddb7dec775e5818ff7ad8ada5",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "3d08eb5131a8a42eb4bd05d7617c177d",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "7c79b8972d6352b4eee0a43a5e44c34d",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "f35515d6561f755a910e464a3ee0195f",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 501994324,
# #         "read2GzippedFileSizeInBytes": 501436393,
# #         "read1OraFileSizeInBytes": 108705055,
# #         "read2OraFileSizeInBytes": 106336466,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401536/L2401536_S21_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401536/L2401536_S21_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401499",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "c3514b3b43fa4085bf8aff71b4ebc99c",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "25c0a9e1e3ab045f8a79c88f5fbec0fb",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "4c93fbe164a171ea968932a5c5704c60",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "d7700d65c048d5ba3216a9c9950f8a74",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 31601361740,
# #         "read2GzippedFileSizeInBytes": 32500865849,
# #         "read1OraFileSizeInBytes": 5680732076,
# #         "read2OraFileSizeInBytes": 6122244909,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401499/L2401499_S17_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401499/L2401499_S17_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401548",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "b2ce15279be6d00b2d5ab503602801f9",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "e060ed8955cbd12c594a64fd38c99a4c",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "2175bb0b70ff73c6363dfdfe788be95b",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "ccaff8c5b79e65283c92664d3e5f98f3",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 40344869450,
# #         "read2GzippedFileSizeInBytes": 43831721872,
# #         "read1OraFileSizeInBytes": 7394266403,
# #         "read2OraFileSizeInBytes": 9748368514,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401548/L2401548_S24_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401548/L2401548_S24_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401535",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "b37e100d62b3c4f8c6b6ff915fa47085",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "55645533f053385edf32fc9b1974151b",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "440edffeae046fe74d985d26858fd212",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "320c81f5760378e0b2c0326f1988a2e9",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 4592850293,
# #         "read2GzippedFileSizeInBytes": 4532211687,
# #         "read1OraFileSizeInBytes": 912733086,
# #         "read2OraFileSizeInBytes": 863814241,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401535/L2401535_S20_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401535/L2401535_S20_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401545",
# #         "lane": 4,
# #         "read1FileRawMd5sum": "20bdacd47f934806826cff64f14137ab",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "a664925ef738144b3ea7fecca7d17c8b",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "d332c60acbf477f5c3ff67ba812ed8cd",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "a839e130511cac8d04c8501af280ea3e",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 1717017,
# #         "read2GzippedFileSizeInBytes": 2075979,
# #         "read1OraFileSizeInBytes": 796634,
# #         "read2OraFileSizeInBytes": 1165743,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401545/L2401545_S23_L004_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_4/L2401545/L2401545_S23_L004_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401546",
# #         "lane": 3,
# #         "read1FileRawMd5sum": "fa4949739bc0cc1e038f755e6dfc935f",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "ba49fca883bbbec90b8ea0d63016703c",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "5d039529fc8b0b3413a1a7433a629d7f",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "bb7c59d8acec52682f48ee926b1e4389",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 40759960531,
# #         "read2GzippedFileSizeInBytes": 43604558126,
# #         "read1OraFileSizeInBytes": 7175776406,
# #         "read2OraFileSizeInBytes": 8928609579,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401546/L2401546_S15_L003_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401546/L2401546_S15_L003_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401542",
# #         "lane": 3,
# #         "read1FileRawMd5sum": "3f45b8e9207c7cfce65c82b8ef704da8",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "f747f7e2029a37f3259b0115d570174c",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "85a35fd245a4136ba9093b489156aaea",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "c40df4c6d54d43520e2a4984050ef903",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 40828499212,
# #         "read2GzippedFileSizeInBytes": 44036500870,
# #         "read1OraFileSizeInBytes": 7251745092,
# #         "read2OraFileSizeInBytes": 9315003236,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401542/L2401542_S13_L003_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401542/L2401542_S13_L003_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401547",
# #         "lane": 3,
# #         "read1FileRawMd5sum": "7489f449122d247a76efd1016b27698c",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "5b17722045c5ad922040d5f83d75e298",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "a8e07545994f8f04480b7448c55d0301",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "4d700b55404518d5d8bc19fb80b4d91a",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 86760295505,
# #         "read2GzippedFileSizeInBytes": 93262377888,
# #         "read1OraFileSizeInBytes": 15309343750,
# #         "read2OraFileSizeInBytes": 19523044745,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401547/L2401547_S16_L003_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401547/L2401547_S16_L003_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401543",
# #         "lane": 3,
# #         "read1FileRawMd5sum": "858a3c75c61c9a6a3ee57bb88e9767d2",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "c6df027a2fd06d07fd5b5f7db3389bea",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "d2fb3773c2892f641ffb9bda8647c540",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "58f4d929cb990b3b47b55863e6e0b3b6",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 75954251054,
# #         "read2GzippedFileSizeInBytes": 82404528509,
# #         "read1OraFileSizeInBytes": 13513480258,
# #         "read2OraFileSizeInBytes": 17848930076,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401543/L2401543_S14_L003_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401543/L2401543_S14_L003_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401544",
# #         "lane": 3,
# #         "read1FileRawMd5sum": "a293c56089c02db4e7f367bdff27523a",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "459851c15d64c58e49f1ed118791745c",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "e8aa34afe2ffbba9fc0e85e0a75a18f0",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "908698d64255f71d0d65ee034c9085ea",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 4850199518,
# #         "read2GzippedFileSizeInBytes": 5205848638,
# #         "read1OraFileSizeInBytes": 882723687,
# #         "read2OraFileSizeInBytes": 1106636114,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401528",
# #         "lane": 1,
# #         "read1FileRawMd5sum": "1a6e08e4f7805b8fd0a92497e8b9273b",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "b994fc1dfd3ddebc5a92b07cb6b69a92",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "d6bebc64de6bb53fa8e5396651e5c1d0",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "f74ff3d37bc18dff494614e6751446ed",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 43357314992,
# #         "read2GzippedFileSizeInBytes": 44092409731,
# #         "read1OraFileSizeInBytes": 8541275179,
# #         "read2OraFileSizeInBytes": 8863424337,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401528/L2401528_S3_L001_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401528/L2401528_S3_L001_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401531",
# #         "lane": 1,
# #         "read1FileRawMd5sum": "f75d74e45d34cd1ae462a42054b43c58",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "02dab4a53141b59d124b3508e2a06e61",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "9a79a240701d5ef5550846d2e7e89252",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "518e6b29cdd676aa792d0dc287aaffd3",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 43818023110,
# #         "read2GzippedFileSizeInBytes": 44844382192,
# #         "read1OraFileSizeInBytes": 8589773627,
# #         "read2OraFileSizeInBytes": 9065337736,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401531/L2401531_S6_L001_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401531/L2401531_S6_L001_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401532",
# #         "lane": 1,
# #         "read1FileRawMd5sum": "418061742b8283ea8d994c1865228e6b",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "a407b0b76df9f1822cd5a88fa9d76162",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "884170f085d518d2b1108a4702cd029d",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "5dba61efadf46f3a6a44db15b5ed29c4",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 4870,
# #         "read2GzippedFileSizeInBytes": 5969,
# #         "read1OraFileSizeInBytes": 4189,
# #         "read2OraFileSizeInBytes": 4914,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401532/L2401532_S7_L001_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401532/L2401532_S7_L001_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401526",
# #         "lane": 1,
# #         "read1FileRawMd5sum": "29ff36a7a31d82a4e6fbf56aaa71c37e",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "dd78b2e398341b5daa58906beca76553",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "81553075806a382b4e432a4868ecf131",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "66c33f6a91430e8290ff8554b4eb21d9",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 42630072057,
# #         "read2GzippedFileSizeInBytes": 43902595265,
# #         "read1OraFileSizeInBytes": 8647052933,
# #         "read2OraFileSizeInBytes": 9265337812,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401526/L2401526_S1_L001_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401526/L2401526_S1_L001_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401530",
# #         "lane": 1,
# #         "read1FileRawMd5sum": "080976d19d4db63755854bf6a6de0b63",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "4db952a4d51f62ae897e1186bd0667dd",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "3c042d89ee4280c1ee7b9e87381651ab",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "ebdad90918f67c7b1e1b755f6beaac37",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 40837628477,
# #         "read2GzippedFileSizeInBytes": 41771419794,
# #         "read1OraFileSizeInBytes": 8127751530,
# #         "read2OraFileSizeInBytes": 8567645785,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401530/L2401530_S5_L001_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401530/L2401530_S5_L001_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401529",
# #         "lane": 1,
# #         "read1FileRawMd5sum": "6edb8a29af315fb7e1bae4fd3fc7ee1c",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "3a46212b10cbff9858f3dd59adcd2230",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "c58b4181c4b8a28ed22831c636eefbc3",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "7424b60deebf0543e9f8c71c52e55512",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 40964945004,
# #         "read2GzippedFileSizeInBytes": 41736727855,
# #         "read1OraFileSizeInBytes": 8158884285,
# #         "read2OraFileSizeInBytes": 8535009518,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401529/L2401529_S4_L001_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401529/L2401529_S4_L001_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401527",
# #         "lane": 1,
# #         "read1FileRawMd5sum": "3dd9eda1e25779ec135a6cae1b0499b0",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "8073b9a378798ca05c225e34856cb7df",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "96af9a95b84170df89e8bb1ed9a8cff9",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "5707dc0a406509e6dc609f9be9aba81a",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 37685523375,
# #         "read2GzippedFileSizeInBytes": 39255037633,
# #         "read1OraFileSizeInBytes": 7599984647,
# #         "read2OraFileSizeInBytes": 8409290279,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401527/L2401527_S2_L001_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_1/L2401527/L2401527_S2_L001_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401541",
# #         "lane": 2,
# #         "read1FileRawMd5sum": "c98185f4e56321381cbef490389145bf",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "065fe4d4a2645420c3725a2465b6b253",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "150aebde6729e5494f885a70f688478a",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "927d3b5cf29205422911126bf2ea3f86",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 79859580981,
# #         "read2GzippedFileSizeInBytes": 84868225988,
# #         "read1OraFileSizeInBytes": 14472788302,
# #         "read2OraFileSizeInBytes": 17716720660,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401541/L2401541_S11_L002_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401541/L2401541_S11_L002_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401538",
# #         "lane": 2,
# #         "read1FileRawMd5sum": "66804083d7972087f7717ea085c3a1b8",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "7048ceefbc53cbf37d44351e1b2f39eb",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "c8ced2ae3c0c7f9f0c3221653cd83bfd",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "675f36b14721d8b2995bdaf8ea2b87d8",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 48811078595,
# #         "read2GzippedFileSizeInBytes": 52362376545,
# #         "read1OraFileSizeInBytes": 8778675617,
# #         "read2OraFileSizeInBytes": 10994671353,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401538/L2401538_S8_L002_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401538/L2401538_S8_L002_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401540",
# #         "lane": 2,
# #         "read1FileRawMd5sum": "8c82101b4bbb4d57a9729571c9a6ac01",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "e4232576c3219c4f5e436353441c02b7",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "cd9a063a333fd27fd4ba4bd482382147",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "7989cc0ca3bed6718c6e9781ca7e5f27",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 37104673601,
# #         "read2GzippedFileSizeInBytes": 39140876826,
# #         "read1OraFileSizeInBytes": 6782972169,
# #         "read2OraFileSizeInBytes": 8108052715,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401540/L2401540_S10_L002_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401540/L2401540_S10_L002_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401539",
# #         "lane": 2,
# #         "read1FileRawMd5sum": "274c55db47de846ca6cc2dc96861366e",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "9c5f494d57e33bc2507ead5e3999941e",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "1aa8f6b2adda58c48777e6ca19ca868d",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "3622162b980acafba6c4cc7c5f841490",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 76151725499,
# #         "read2GzippedFileSizeInBytes": 81298319647,
# #         "read1OraFileSizeInBytes": 13777362811,
# #         "read2OraFileSizeInBytes": 17019842335,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401539/L2401539_S9_L002_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401539/L2401539_S9_L002_R2_001.fastq.ora"
# #     },
# #     {
# #         "rgsm": "L2401544",
# #         "lane": 2,
# #         "read1FileRawMd5sum": "fd45570ebced2ff8e53a81dd5bedc258",  # pragma: allowlist secret
# #         "read2FileRawMd5sum": "5aa64f276ccf757126dd0e3346d9011f",  # pragma: allowlist secret
# #         "read1FileOraMd5sum": "128e45b1cbbbdf04640df017efe130fa",  # pragma: allowlist secret
# #         "read2FileOraMd5sum": "a5686b1cb274911e14ab4cb8620f8c38",  # pragma: allowlist secret
# #         "read1GzippedFileSizeInBytes": 4479234306,
# #         "read2GzippedFileSizeInBytes": 4788152749,
# #         "read1OraFileSizeInBytes": 836174432,
# #         "read2OraFileSizeInBytes": 1029001113,
# #         "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
# #         "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ora-compression/241024_A00130_0336_BHW7MVDSXC/202411156290aa4i/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora"
# #     }
# # ]