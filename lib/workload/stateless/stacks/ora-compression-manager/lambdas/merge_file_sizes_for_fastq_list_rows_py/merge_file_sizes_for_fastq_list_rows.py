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
    with read_icav2_file_contents(project_data.project_id, project_data.data.id) as file_contents:
        return pd.read_csv(
            StringIO(file_contents),
            header=None,
            names=["md5sum", "file_name"],
            sep="  ",
            engine="python"
        )


def read_file_sizes(project_data: ProjectData) -> pd.DataFrame:
    with read_icav2_file_contents(project_data.project_id, project_data.data.id) as file_contents:
        return pd.read_csv(
            StringIO(file_contents),
            sep="\t"
        )


def read_fastq_list_csv(project_data: ProjectData) -> pd.DataFrame:
    """
    Read the csv from the icav2
    :param project_data:
    :return:
    """
    with read_icav2_file_contents(project_data.project_id, project_data.data.id) as file_contents:
        return pd.read_csv(StringIO(file_contents))


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
        fastq_gzipped_md5_df: pd.DataFrame,
        fastq_ora_md5_df: pd.DataFrame,
        fastq_gzipped_filesizes_df: pd.DataFrame,
        fastq_ora_filesizes_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Given the fastq list rows, the md5sums and the file sizes, merge them together
    :param fastq_list_ora_df:
    :param fastq_gzipped_md5_df:
    :param fastq_ora_md5_df:
    :param fastq_gzipped_filesizes_df:
    :param fastq_ora_filesizes_df:
    :return:
    """
    # Extend the gzipped md5s to the fastq list rows
    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_gzipped_md5_df,
        how="left",
        left_on="read1File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"md5sum": "read1FileGzippedMd5sum"}
    ).merge(
        fastq_gzipped_md5_df,
        how="left",
        left_on="read2File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"md5sum": "read2FileGzippedMd5sum"}
    )

    # Extend the ora md5s to the fastq list rows
    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_ora_md5_df,
        how="left",
        left_on="read1File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"md5sum": "read1FileOraMd5sum"}
    ).merge(
        fastq_ora_md5_df,
        how="left",
        left_on="read2File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"md5sum": "read2FileOraMd5sum"}
    )

    # Extend the gzipped file sizes to the fastq list rows
    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_gzipped_filesizes_df,
        how="left",
        left_on="read1File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"fileSize": "read1GzippedFileSize"}
    ).merge(
        fastq_gzipped_filesizes_df,
        how="left",
        left_on="read2File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"fileSize": "read2GzippedFileSize"}
    )

    fastq_list_ora_df = fastq_list_ora_df.merge(
        fastq_ora_filesizes_df,
        how="left",
        left_on="read1File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"fileSize": "read1OraFileSize"}
    ).merge(
        fastq_ora_filesizes_df,
        how="left",
        left_on="read2File",
        right_on="fileName"
    ).drop(
        columns='fileName'
    ).rename(
        columns={"fileSize": "read2OraFileSize"}
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
            "fastq_gzipped_md5.txt")
    )

    # Get the file sizes for the new ora compressed tsv
    fastq_ora_md5_file_obj = read_md5sum(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_ora_md5.txt")
    )

    # Get the original gzipped tsv file size
    fastq_gzipped_filesizes_file_obj = read_file_sizes(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
    "fastq_gzipped_filesizes.tsv"
        )
    )

    # Get the md5sum txts for both the fastq gzipped and ora files
    fastq_ora_filesizes_file_obj = read_file_sizes(
        get_icav2_file_from_folder(
            output_dir_project_data_list,
            "fastq_ora_filesizes.tsv"
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

    # Return the merged file as a json list
    return fastq_list_ora_df.to_dict(orient="records")
