#!/usr/bin/env python3

"""
Metadata handlers
"""

# Standard Libraries
import typing
from typing import Union
import boto3
from botocore.client import BaseClient

# Internal Libraries
from .logger import get_logger

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient


logger = get_logger()


def get_boto3_session() -> boto3.Session:
    """
    Get a regular boto3 session
    :return:
    """
    return boto3.session.Session()


def get_aws_region() -> str:
    """
    Get AWS region using boto3
    :return:
    """
    boto3_session = get_boto3_session()
    return boto3_session.region_name


def get_boto3_ssm_client() -> Union['SSMClient', BaseClient]:
    return boto3.client("ssm")


# def get_portal_base_url() -> str:
#     ssm_client: SSMClient = get_boto3_ssm_client()
#
#     return ssm_client.get_parameter(
#         Name=PORTAL_API_BASE_URL_SSM_PATH
#     ).get("Parameter").get("Value")
#
#
# def get_portal_creds(portal_base_url: str) -> BotoAWSRequestsAuth:
#     """
#     Get the credentials for hitting the data portal apis.
#     :return:
#     """
#     return BotoAWSRequestsAuth(
#         aws_host=urlparse(portal_base_url).hostname,
#         aws_region=get_aws_region(),
#         aws_service='execute-api',
#     )


# def get_metadatadata_information_from_portal_for_library_id(library_id: str) -> pd.DataFrame:
#     """
#     Get the required information from the data portal
#     * External Sample ID -> External Specimen ID
#     * External Subject ID -> Patient URN
#     :param library_id:
#     :return: A pandas DataFrame with the following columns:
#       * library_id
#       * project_name
#       * external_sample_id
#       * external_subject_id
#     """
#
#     portal_base_url = get_portal_base_url()
#     portal_url_endpoint = PORTAL_METADATA_ENDPOINT.format(
#         PORTAL_API_BASE_URL=portal_base_url
#     )
#     portal_auth = get_portal_creds(portal_url_endpoint)
#
#     req: Response = requests.get(
#         url=portal_url_endpoint,
#         auth=portal_auth,
#         params={
#             "library_id": library_id
#         }
#     )
#
#     req_dict: Dict = req.json()
#
#     results: List
#     if (results := req_dict.get("results", None)) is None:
#         logger.error(f"Did not get any results on {portal_url_endpoint}, "
#                      f"library id: {library_id}")
#         raise AttributeError
#
#     # Check length of results
#     if not len(results) == 1:
#         logger.error(f"Expected only one entry for library id: {library_id}")
#         raise ValueError
#
#     result: Dict = results[0]
#
#     # Ensure the expected keys are present
#     # field: str
#     # for field in PORTAL_FIELDS:
#     #     if field not in result.keys():
#     #         logger.error(f"Expected {field} in portal metadata query but only got {list(result.keys())}")
#
#     # return pd.DataFrame([result])[PORTAL_FIELDS]
#     return pd.DataFrame([result])


# This code is deprecated and no longer in use
# from .samplesheet_helper import get_library_assay_from_samplesheet_dict
# def get_library_id_assay(library_id: str, samplesheet_dict: Dict) -> Optional[str]:
#     """
#     Returns the assay type for a given library id
#     :param library_id:
#     :return:
#     """
#     try:
#         return get_library_assay_from_samplesheet_dict(library_id, samplesheet_dict)
#     except ValueError:
#         return None
#     #
#     # try:
#     #     return get_metadatadata_information_from_portal_for_library_id(library_id)["assay"].unique().item()
#     # except:
#     #     # FIXME - workaround while we wait for the portal to be updated
#     #     return "WGS"
