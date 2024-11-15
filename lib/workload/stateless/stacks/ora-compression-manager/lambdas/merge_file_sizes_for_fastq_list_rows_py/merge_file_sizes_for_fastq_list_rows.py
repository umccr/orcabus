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
from wrapica.enums import DataType
from wrapica.project_data import (
    ProjectData,
    convert_uri_to_project_data_obj,
    list_project_data_non_recursively,
    read_icav2_file_contents
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
            "fastq_gzipped.md5.txt")
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
#                     "output_dir_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # [
#     #     {
#     #         "rgsm": "L2401526",
#     #         "lane": 1,
#     #         "read1FileRawMd5sum": "ff9f75053fd5dfe34ac011fd679c62dd",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "18a267c2c5ca2f71e272815cd7508fd8",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "bb26321f461de85419c95131ce73f0a5",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "986ef94789f76d7a5e510d34b465033b",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 42630072057,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 43902595265,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 8647052933,
#     #         "read2OraFileSizeInBytes": 9265337812,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401526/L2401526_S1_L001_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401526/L2401526_S1_L001_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401532",
#     #         "lane": 1,
#     #         "read1FileRawMd5sum": "7ec0a49be2a3c0a049b7593d00474cdb",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "af902803801285d3475ef1c8776ad611",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "6e2c5ce6e3014fd5f8be78bf9d769b26",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "54c5a6787ab80f07c25fc4abd5eb6bbc",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 4870,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 5969,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 4189,
#     #         "read2OraFileSizeInBytes": 4914,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401532/L2401532_S7_L001_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401532/L2401532_S7_L001_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401528",
#     #         "lane": 1,
#     #         "read1FileRawMd5sum": "6de45d4c93afcf310d45c0edb0361427",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "c9a3dfed465b4053e1bacbc9e1b6bc70",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "1b947ed0f912f5dc0d5246cf0cbe63b9",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "16e8dc8d559dd8dd9515946c5112021c",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 43357314992,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 44092409731,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 8541275179,
#     #         "read2OraFileSizeInBytes": 8863424337,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401528/L2401528_S3_L001_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401528/L2401528_S3_L001_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401531",
#     #         "lane": 1,
#     #         "read1FileRawMd5sum": "6dd394650558c4a93e2e2dd0322eaf08",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "f8ccf03414fc374903b1a2a5302ac517",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "1c61d4cca313a29dab5a05c2b9173a93",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "14583d8caca26fda8fac0701c0588292",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 43818023110,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 44844382192,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 8589773627,
#     #         "read2OraFileSizeInBytes": 9065337736,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401531/L2401531_S6_L001_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401531/L2401531_S6_L001_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401527",
#     #         "lane": 1,
#     #         "read1FileRawMd5sum": "0953e17b02574f3167abbaba37dcd4ef",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "4d7f065b4ba5f7a702a469d566403bc6",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "70e9b68355b87e6fc3d96871def6e881",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "f3d0b90486c6f77fd78832777972b1be",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 37685523375,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 39255037633,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 7599984647,
#     #         "read2OraFileSizeInBytes": 8409290279,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401527/L2401527_S2_L001_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401527/L2401527_S2_L001_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401530",
#     #         "lane": 1,
#     #         "read1FileRawMd5sum": "cd9e0018d17f119871e3b34ee5c6cf78",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "b4d9ab7d12e752eef790f27dd7d68aa5",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "9f2eb09791defb77c40e54693301d327",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "81434c21c81358e2d454750d428912ac",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 40837628477,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 41771419794,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 8127751530,
#     #         "read2OraFileSizeInBytes": 8567645785,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401530/L2401530_S5_L001_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401530/L2401530_S5_L001_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401529",
#     #         "lane": 1,
#     #         "read1FileRawMd5sum": "69b4f91a0c87e52a5f02186d61f58f5d",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "5c42766421250fcbb97944d7e0920cc0",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "26cd69ff20668ca692f4fbc043bbfba6",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "09442fbd28bbf53778b71eeed1223027",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 40964945004,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 41736727855,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 8158884285,
#     #         "read2OraFileSizeInBytes": 8535009518,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401529/L2401529_S4_L001_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_1/L2401529/L2401529_S4_L001_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401539",
#     #         "lane": 2,
#     #         "read1FileRawMd5sum": "1cf861134c39c7a1fe885396de951fd9",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "8f97bf9c1fcbb364d7779d9bdaba7e12",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "833cd38bea126e644627694af39e551b",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "31bda754f678a2c1d39cb7484eafc28b",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 76151725499,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 81298319647,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 13777362811,
#     #         "read2OraFileSizeInBytes": 17019842335,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401539/L2401539_S9_L002_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401539/L2401539_S9_L002_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401544",
#     #         "lane": 2,
#     #         "read1FileRawMd5sum": "a6e1b6243503bfdffb15389be16a8300",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "6e08a07e72f14a59b663bec92d060960",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "6acbc7678701e00a7918932729a76d9c",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "71fc9c563ab6b1292a60a63919fe47b8",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 4479234306,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 4788152749,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 836174432,
#     #         "read2OraFileSizeInBytes": 1029001113,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401540",
#     #         "lane": 2,
#     #         "read1FileRawMd5sum": "c45c22d932e8c2d4501663779f0b745a",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "3b4c5bc5b1001bd171302d01e676eb0b",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "0de3746eab5f548936fb5d1708e0e329",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "e52be348378672ca5929e4a27a0f4d88",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 37104673601,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 39140876826,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 6782972169,
#     #         "read2OraFileSizeInBytes": 8108052715,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401540/L2401540_S10_L002_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401540/L2401540_S10_L002_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401538",
#     #         "lane": 2,
#     #         "read1FileRawMd5sum": "fd5aa3bce601adfdad0d7d5b7a057dae",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "d62a9e486cee349f3815393ce39f74d6",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "a0300d16e659784a6c7e1fdc1e07c758",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "a5cbe8fcb140fc739de8e14c732c00d8",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 48811078595,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 52362376545,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 8778675617,
#     #         "read2OraFileSizeInBytes": 10994671353,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401538/L2401538_S8_L002_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401538/L2401538_S8_L002_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401541",
#     #         "lane": 2,
#     #         "read1FileRawMd5sum": "a8c7ef1c26e6d1f45322573ddcbf0f43",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "855832733f5bec03edb713af77bf5c56",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "ad152e6d64994a5b979a8da5c22b1162",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "a64a55a3060c020a8b336abaf3859d4a",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 79859580981,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 84868225988,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 14472788302,
#     #         "read2OraFileSizeInBytes": 17716720660,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401541/L2401541_S11_L002_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_2/L2401541/L2401541_S11_L002_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401544",
#     #         "lane": 3,
#     #         "read1FileRawMd5sum": "01144e91f95713e33c3c601e884953f6",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "c2bb45d50802ed331a1aa5b84e9a3567",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "f959dc44f6049aaa0455f9be19cb5e96",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "55630173730476750a60cfc09237aa58",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 4850199518,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 5205848638,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 882723687,
#     #         "read2OraFileSizeInBytes": 1106636114,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401543",
#     #         "lane": 3,
#     #         "read1FileRawMd5sum": "a3d78547cfb81248ccf691b25695ea2f",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "36491c11fc8f70dc6fe4a689c8328dfb",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "4379cdba30cd66dc00f5ee656e6406fa",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "61c5f092d6ed26734c629c0b3e3edbee",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 75954251054,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 82404528509,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 13513480258,
#     #         "read2OraFileSizeInBytes": 17848930076,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401543/L2401543_S14_L003_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401543/L2401543_S14_L003_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401547",
#     #         "lane": 3,
#     #         "read1FileRawMd5sum": "d4dea3f865c97dc4a211a4b5516d2cd4",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "8a8b5164e0d2fe7b0781598c097d4752",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "c9d8b466877cc812f2ebbee77bf21f4a",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "9ed9e112cbf77f59afc8df6cea61eb4c",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 86760295505,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 93262377888,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 15309343750,
#     #         "read2OraFileSizeInBytes": 19523044745,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401547/L2401547_S16_L003_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401547/L2401547_S16_L003_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401542",
#     #         "lane": 3,
#     #         "read1FileRawMd5sum": "b90d2ff9c255519a64ee5163688c721c",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "5c3ad35d21d25152e0b1b8973358e660",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "229e76982a4b90e50d176c5f6c9cf6ad",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "4126386d832c12d2393759a22857949c",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 40828499212,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 44036500870,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 7251745092,
#     #         "read2OraFileSizeInBytes": 9315003236,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401542/L2401542_S13_L003_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401542/L2401542_S13_L003_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401546",
#     #         "lane": 3,
#     #         "read1FileRawMd5sum": "cba424c2f9dee702dc6a64a70ad68f81",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "ad331f601cc96117f3db794460126b8e",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "053d9ca034d2cdd7539144295e583ce5",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "f28fb5e6b0087edaf4e2c26a16e605f3",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 40759960531,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 43604558126,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 7175776406,
#     #         "read2OraFileSizeInBytes": 8928609579,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401546/L2401546_S15_L003_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_3/L2401546/L2401546_S15_L003_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401537",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "f2f18f5dff7dce7e118ef61833ff51c8",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "f90ee88763865873dcaaf6e04162964f",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "ff27530bfd372e3008f45429b271b0ca",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "79694fa527e5e3c59a156e09b92c8e53",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 57604117,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 58247458,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 20303567,
#     #         "read2OraFileSizeInBytes": 20866911,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401537/L2401537_S22_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401537/L2401537_S22_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401553",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "79f78fb976346efbd560cec9bbafd88d",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "9808e155473c766661f95a277306cb1a",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "f09eb0ca7ce678bbc2e7bb09cb5ebcb9",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "0c997dbe96adc7c1beb34416d052cdf3",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 35683061339,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 38483719785,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 6617978068,
#     #         "read2OraFileSizeInBytes": 8629405567,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401553/L2401553_S27_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401553/L2401553_S27_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401549",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "ff922a5d65f93f38e485e6ea8da1d770",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "c4af49c86f576dbb82b58b4db13f6046",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "1ae324e09bfd67c71abcf68005fe3cda",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "1f0a4c24b4cea13412250d92c2dbbb65",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 86165891313,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 92043170392,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 15540038685,
#     #         "read2OraFileSizeInBytes": 19403308615,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401549/L2401549_S25_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401549/L2401549_S25_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401534",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "b6e5e8a16e92abd76eae33cd347c6191",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "2a269b78b37ae188f664a673081085a1",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "95bb938dab7f366c2eb6a780873a4039",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "fccd14d34831d34b9ba48c17e53933a9",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 6628903368,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 6559410472,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 1299905533,
#     #         "read2OraFileSizeInBytes": 1238284291,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401534/L2401534_S19_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401534/L2401534_S19_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401533",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "c7f5be35252703b2d5b596e608e9d01b",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "8d0cae172acfd63ef8cd9a000bb59be7",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "f38df2aafd432cf49eb608da422cd7f3",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "f34ed206348221529dc79eadea940250",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 6179483185,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 6065388584,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 1209397423,
#     #         "read2OraFileSizeInBytes": 1129072555,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401533/L2401533_S18_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401533/L2401533_S18_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401552",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "a32f53cd103868e9000d105a6e907cde",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "15963cfcd84d2ee0326a10ada72e204c",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "69c89690e2a0a7c5585b3967c8cb6bca",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "611bd48574d9e684031d09b94dc21a15",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 33237582408,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 36766116815,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 6123700775,
#     #         "read2OraFileSizeInBytes": 8612068652,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401552/L2401552_S26_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401552/L2401552_S26_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401536",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "d278e8dc93355cceb54e38e128075989",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "bc5a290c4cdd223abde54714c9c16245",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "76ca92e1017fad3c2d372e2199a333a8",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "1d0460fa288bbc3e9230b94f6ff0e664",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 501994324,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 501436393,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 108705055,
#     #         "read2OraFileSizeInBytes": 106336466,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401536/L2401536_S21_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401536/L2401536_S21_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401545",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "68efe19804293a725fd41bd94878d378",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "9006f2e7db1b0cf9e640d3f60c20d6d3",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "cf9e7482431174d17f710fd94e3ae972",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "acc3bf20a8b03283fb66edc41fd65c7a",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 1717017,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 2075979,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 796634,
#     #         "read2OraFileSizeInBytes": 1165743,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401545/L2401545_S23_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401545/L2401545_S23_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401535",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "313a6608fba6b5fd7fdd830eace645c1",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "4260bd94f0e2f2e961bc3aaf3e0e9851",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "624e816beb856153d35e8a71478277ea",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "201607c4b04536c07e0b5514d961e56e",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 4592850293,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 4532211687,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 912733086,
#     #         "read2OraFileSizeInBytes": 863814241,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401535/L2401535_S20_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401535/L2401535_S20_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401548",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "c32a0f8a097796431462a4942106159f",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "3ab0eb6b307b0138a3c086b0ddd395dd",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "39dff48606c97a86deb048a9c3a367ee",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "3020cb923c39f0a75fa26030b88c3ade",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 40344869450,  # pragma: allowlist secret
#     #         "read2GzippedFileSizeInBytes": 43831721872,  # pragma: allowlist secret
#     #         "read1OraFileSizeInBytes": 7394266403,
#     #         "read2OraFileSizeInBytes": 9748368514,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401548/L2401548_S24_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401548/L2401548_S24_L004_R2_001.fastq.ora"
#     #     },
#     #     {
#     #         "rgsm": "L2401499",
#     #         "lane": 4,
#     #         "read1FileRawMd5sum": "dbf0cdca626f00e95f327e377f25e3d4",  # pragma: allowlist secret
#     #         "read2FileRawMd5sum": "d4fae1544cb032110dc02c5c1a676eed",  # pragma: allowlist secret
#     #         "read1FileOraMd5sum": "47987c5ea8fa2aa8d73af6ca0719e587",  # pragma: allowlist secret
#     #         "read2FileOraMd5sum": "2fb0307a88b882e0bdd29b16e5367cb6",  # pragma: allowlist secret
#     #         "read1GzippedFileSizeInBytes": 31601361740,
#     #         "read2GzippedFileSizeInBytes": 32500865849,
#     #         "read1OraFileSizeInBytes": 5680732076,
#     #         "read2OraFileSizeInBytes": 6122244909,
#     #         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401499/L2401499_S17_L004_R1_001.fastq.ora",
#     #         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411046290aa4g/241024_A00130_0336_BHW7MVDSXC/Samples/Lane_4/L2401499/L2401499_S17_L004_R2_001.fastq.ora"
#     #     }
#     # ]