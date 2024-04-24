#!/usr/bin/env python3

"""

"""
from pathlib import Path
from urllib.parse import urlparse

from libica.openapi.libgds import (
    ApiClient, FilesApi, CreateFileRequest, ApiException, FileWriteableResponse, ObjectStoreAccess, FileResponse
)

import logging


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def get_file_obj_from_file_path(gds_path: str) -> FileResponse:
    from .ica_config_helpers import get_ica_gds_configuration

    with ApiClient(get_ica_gds_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = FilesApi(api_client)

    try:
        # Get file entry in GDS
        api_response = api_instance.list_files(
            volume_name=[urlparse(gds_path).netloc],
            path=[str(Path(urlparse(gds_path).path))],
            recursive=False,
            include="PresignedUrl"
        )

    except ApiException as e:
        logger.error("Exception when calling FilesApi->get_file_by_path: %s\n" % e)
        raise e

    if not len(api_response.items) == 1:
        raise ValueError(f"File not found: {gds_path}")

    return api_response.items[0]


def get_new_file_access_credentials(gds_path: str) -> ObjectStoreAccess:
    from .ica_config_helpers import get_ica_gds_configuration

    with ApiClient(get_ica_gds_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = FilesApi(api_client)

    body = CreateFileRequest(
        name=Path(urlparse(gds_path).path).name,
        volume_name=urlparse(gds_path).netloc,
        folder_path=str(Path(urlparse(gds_path).path).parent) + "/",
        type="text/plain"
    )  # CreateFileRequest |
    include = 'ObjectStoreAccess'  # str | Optionally include additional fields in the response.              Possible values: ObjectStoreAccess (optional)

    try:
        # Create a file entry in GDS and get temporary credentials for upload
        api_response: FileWriteableResponse = api_instance.create_file(body, include=include)
    except ApiException as e:
        logger.error("Exception when calling FilesApi->create_file: %s\n" % e)
        raise e

    return api_response.object_store_access


def upload_file_to_gds(local_path: Path, gds_path: str):
    from .aws_s3_helpers import upload_file_to_s3

    access_credentials: ObjectStoreAccess = get_new_file_access_credentials(gds_path)
    access_key_id = access_credentials.aws_s3_temporary_upload_credentials.access_key_id
    secret_access_key = access_credentials.aws_s3_temporary_upload_credentials.secret_access_key
    session_token = access_credentials.aws_s3_temporary_upload_credentials.session_token
    bucket_name = access_credentials.aws_s3_temporary_upload_credentials.bucket_name
    key_prefix = access_credentials.aws_s3_temporary_upload_credentials.key_prefix

    upload_file_to_s3(
        local_path=local_path,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        bucket_name=bucket_name,
        key_prefix=key_prefix
    )


def download_file_from_gds(
    gds_path: str,
    local_path: Path,
):
    # Generate the presigned url
    file_presigned_url = get_file_obj_from_file_path(gds_path).presigned_url

    # Download file from GDS using the requests library
    import requests
    with open(local_path, 'wb') as f_h:
        f_h.write(requests.get(file_presigned_url).content)


# if __name__ == '__main__':
#     os.environ["ICA_ACCESS_TOKEN_SECRET_ID"] = "IcaSecretsPortal"
#     os.environ["ICA_BASE_URL"] = "https://aps2.platform.illumina.com"
#     set_ica_env_vars()
#     download_file_from_gds(
#         "gds://development/temp/alexis/_tags.json",
#         Path("foo.txt")
#     )
