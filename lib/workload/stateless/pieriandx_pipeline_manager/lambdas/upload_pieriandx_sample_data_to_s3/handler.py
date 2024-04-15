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

from tempfile import TemporaryDirectory
from pathlib import Path
from urllib.parse import urlparse
from wrapica.project_data import read_icav2_file_contents, convert_icav2_uri_to_data_obj

from pieriandx_pipeline_tools.utils.s3_helpers import set_s3_access_cred_env_vars, upload_file
from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_icav2_env_vars
from pieriandx_pipeline_tools.utils.compression_helpers import decompress_file


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
        icav2_data_obj = convert_icav2_uri_to_data_obj(event.get("src_uri"))

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

            # Upload to s3
            upload_file(dest_bucket, dest_key, output_path)
    else:
        contents = event.get("contents")

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / Path(dest_key).name
            output_path.write_text(contents)

            upload_file(dest_bucket, dest_key, output_path)


if __name__ == "__main__":
    handler(
        {
            "contents": "[Header]\nFileFormatVersion,2\nRunName,Tsqn-NebRNA231113-MLeeSTR_16Nov23\nInstrumentType,NovaSeq\n\n[Reads]\nRead1Cycles,151\nRead2Cycles,151\nIndex1Cycles,10\nIndex2Cycles,10\n\n[TSO500L_Settings]\nAdapterRead1,CTGTCTCTTATACACATCT\nAdapterRead2,CTGTCTCTTATACACATCT\nAdapterBehaviour,trim\nMinimumTrimmedReadLength,35\nMaskShortReads,35\nOverrideCycles,U7N1Y143;I10;I10;U7N1Y143\n\n[TSO500L_Data]\nSample_ID,Sample_Type,Lane,Index,Index2,I7_Index_ID,I5_Index_ID\nL2301368,DNA,1,GACTGAGTAG,CACTATCAAC,UDP0009,UDP0009\n",
            "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04405__L2301368__ot__003__20240415abcd0001/SampleSheet.csv"
        },
        None
    )
