#!/usr/bin/env python3

"""

Upload a file to pieriandx sample data s3 bucket

Given an icav2 uri, and a destination uri, download and upload the file into the destination uri

If needs_decompression is set to true, the downloaded file will be decompressed before uploading

Environment variables required are:
PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID -> The secret id for the s3 access credentials
ICAV2_ACCESS_TOKEN_SECRET_ID -> The secret id for the icav2 access token

Input will look like this

{
  "src_uri": "icav2://project-id/path/to/sample-microsat_output.txt",
  "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368.microsat_output.json",
  "needs_decompression": false,
  "contents": null
}

"""

# Standard imports
from tempfile import TemporaryDirectory
from pathlib import Path
from urllib.parse import urlparse
from wrapica.project_data import read_icav2_file_contents, convert_uri_to_project_data_obj
import logging

# Layer imports
from pieriandx_pipeline_tools.utils.s3_helpers import set_s3_access_cred_env_vars, upload_file
from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_icav2_env_vars
from pieriandx_pipeline_tools.utils.compression_helpers import decompress_file

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Upload pieriandx sample data to s3 bucket
    Args:
        event:
        context:

    Returns:

    """

    # Set env vars
    set_icav2_env_vars()
    set_s3_access_cred_env_vars()

    # Get uris
    needs_decompression = event.get("needs_decompression", False)
    dest_uri = event.get("dest_uri")
    dest_bucket = urlparse(dest_uri).netloc
    dest_key = urlparse(dest_uri).path

    if event.get("src_uri", None) is not None:
        icav2_data_obj = convert_uri_to_project_data_obj(event.get("src_uri"))

        with TemporaryDirectory() as temp_dir:
            # Set output path
            output_path = Path(temp_dir) / icav2_data_obj.data.details.name

            # Read icav2 file contents
            read_icav2_file_contents(
                project_id=icav2_data_obj.project_id,
                data_id=icav2_data_obj.data.id,
                output_path=output_path
            )

            if needs_decompression:
                decompress_file(output_path, output_path.parent / output_path.name.replace(".gz", ""))
                output_path = output_path.parent / output_path.name.replace(".gz", "")

            if output_path.name.endswith("MetricsOutput.tsv"):
                with open(output_path, "r") as f:
                    contents = f.read()
                contents = contents.replace('[Run QC Metrics]', '[Run Metrics]')
                with open(output_path, "w") as f:
                    f.write(contents)

            # Upload to s3
            upload_file(dest_bucket, dest_key, output_path)
    else:
        contents = event.get("contents")

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / Path(dest_key).name
            output_path.write_text(contents)

            upload_file(dest_bucket, dest_key, output_path)


# if __name__ == "__main__":
#     from os import environ
#     environ["AWS_PROFILE"] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ["ICAV2_ACCESS_TOKEN_SECRET_ID"] = "ICAv2JWTKey-umccr-prod-service-dev"
#     environ['PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID'] = "PierianDx/S3Credentials"
#
#     handler(
#         {
#           "needs_decompression": False,
#           "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161_MetricsOutput.tsv",
#           "contents": None,
#           "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2400161__V2__abcd1235__abcd1234/Data/Intensities/BaseCalls/L2400161_MetricsOutput.tsv"
#         },
#         None
#     )

# if __name__ == "__main__":
#     from os import environ
#     environ["AWS_PROFILE"] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ["ICAV2_ACCESS_TOKEN_SECRET_ID"] = "ICAv2JWTKey-umccr-prod-service-production"
#     environ['PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID'] = "PierianDx/S3Credentials"
#
#     handler(
#         {
#           "needs_decompression": False,
#           "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560_MetricsOutput.tsv",
#           "contents": None,
#           "dest_uri": "s3://pdx-xfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560_MetricsOutput.tsv"
#         },
#         None
#     )
#
