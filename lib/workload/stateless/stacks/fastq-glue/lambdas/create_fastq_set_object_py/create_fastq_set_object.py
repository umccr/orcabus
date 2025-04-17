#!/usr/bin/env python3

"""
Given inputs for a fastq set object, create the fastq set object

* instrumentRunId
* sampleBclConvertData:
  * libraryId
  * index
  * lane
  * cycleCount
* sampleFileNames
  * libraryId
  * lane
  * read1FileUri
  * read2FileUri
* sampleDemuxStats
  * libraryId
  * lane
  * readCount

We calculate the base count estimate from the read count and cycle count

The fastq set object has the following structure:
{
  "library": {
    "libraryId": "<libraryId>",
  },
  "allowAdditionalFastq": false,
  "isCurrentFastqSet": true,
  "fastqSet": [
    < For each libraryId + lane combination >
    {
      "index": "<index>",
      "lane": 1,
      "instrumentRunId": "<instrumentRunId>",
      "library": {
        "libraryId": "<libraryId>"
      },
      "platform": "Illumina",
      "center": "UMCCR",
      "date": "<instrument run id date in YYYY-MM-DD format>",
      "readSet": {
        "r1": {
          "s3Uri": "<read1FileUri>",
        },
        "r2": {
          "s3Uri": "<read2FileUri>",
        },
        "compressionFormat": "GZIP if read1FileUri endswith '.gz' else 'ORA'"
      },
      "readCount": <readCount>,
      "baseCountEst": <readCount * cycleCount>,
      "isValid": true,
    }
  ]
}

"""
import typing
from typing import Optional, List
from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
import boto3
import re
import json

# Imports
import pandas as pd
from datetime import datetime

from gspread_pandas import Spread

# Layer imports
from fastq_tools import (
    create_fastq_set_object, FastqSet,
    create_fastq_list_row_object, allow_additional_fastqs_to_fastq_set,
    disallow_additional_fastqs_to_fastq_set,
    link_fastq_list_row_to_fastq_set,
    set_is_not_current_fastq_set, FastqListRow
)
from fastq_tools.utils.query_helpers import get_fastq_sets

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient

# Globals
DEFAULT_PLATFORM = "Illumina"
DEFAULT_CENTER = "UMCCR"

# For emergency use only!
# Currently no way to distinguish between topups and rerun
# Solution is to use the metadata tracking sheet
GDRIVE_AUTH_JSON_SSM_PARAMETER_PATH_ENV_VAR = "GDRIVE_AUTH_JSON_SSM_PARAMETER_PATH"
METADATA_TRACKING_SHEET_ID_SSM_PARAMETER_PATH_ENV_VAR = "METADATA_TRACKING_SHEET_ID_SSM_PARAMETER_PATH"
GET_YEAR_FROM_LIBRARY_ID_REGEX = re.compile(r"L(?:PRJ)?(\d{2})(?:\d{5})?")



def merge_dataframes(
        bclconvert_data_df: pd.DataFrame,
        filenames_df: pd.DataFrame,
        demux_stats_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge the three dataframes on libraryId and lane

    Output columns are as follows:
    * libraryId
    * lane
    * index
    * cycleCount
    * read1FileUri
    * read2FileUri
    * readCount
    """
    merged_df = pd.merge(
        bclconvert_data_df,
        filenames_df,
        on=["libraryId", "lane"],
        how="inner",
    )
    merged_df = pd.merge(
        merged_df,
        demux_stats_df,
        on=["libraryId", "lane"],
        how="inner",
    )
    return merged_df


def generate_fastq_list_row_list_from_inputs(
        instrument_run_id: str,
        bclconvert_data_df: pd.DataFrame,
        filenames_df: pd.DataFrame,
        demux_stats_df: pd.DataFrame,
) -> List[FastqListRow]:
    merged_df = merge_dataframes(bclconvert_data_df, filenames_df, demux_stats_df)

    return list(map(
        lambda index_row_iter_: create_fastq_list_row_object(
            {
                "index": index_row_iter_[1]["index"],
                "lane": index_row_iter_[1]["lane"],
                "instrumentRunId": instrument_run_id,
                "library": {
                    "libraryId": index_row_iter_[1]["libraryId"]
                },
                "platform": DEFAULT_PLATFORM,
                "center": DEFAULT_CENTER,
                # Convert 250320_A01052_0256_BHFCFCDSXF
                # To 2025-03-20
                "date": (
                    datetime.strptime(
                        instrument_run_id.split("_")[0],
                        "%y%m%d"
                    ).strftime(
                        "%Y-%m-%d"
                    )
                ),
                # Generate readset
                # But consider that the read2FileUri may not exist
                "readSet": dict(filter(
                    lambda kv: kv[1] is not None,
                    {
                        "r1": {
                            "s3Uri": index_row_iter_[1]["read1FileUri"],
                        },
                        "r2": {
                            "s3Uri": index_row_iter_[1].get("read2FileUri", None),
                        },
                        "compressionFormat": "GZIP" if index_row_iter_[1]["read1FileUri"].endswith(
                            ".gz") else "ORA",
                    }.items()
                )),
                "readCount": index_row_iter_[1]["readCount"],
                "baseCountEst": (index_row_iter_[1]["readCount"] * index_row_iter_[1]["cycleCount"]),
                "isValid": True,
            }
        ),
        merged_df.iterrows()
    ))


def create_fastq_set_from_df(
        merged_df: pd.DataFrame,
        instrument_run_id: str,
) -> FastqSet:
    """
    From the merged dataframe, create the fastq set object
    :param merged_df:
    :return:
    """
    return create_fastq_set_object(
        {
            "library": {
                "libraryId": merged_df["libraryId"].unique().item(),
            },
            "allowAdditionalFastq": False,
            "isCurrentFastqSet": True,
            "fastqSet": list(map(
                lambda index_row_iter_: {
                    "index": index_row_iter_[1]["index"],
                    "lane": index_row_iter_[1]["lane"],
                    "instrumentRunId": instrument_run_id,
                    "library": {
                        "libraryId": index_row_iter_[1]["libraryId"]
                    },
                    "platform": DEFAULT_PLATFORM,
                    "center": DEFAULT_CENTER,
                    # Convert 250320_A01052_0256_BHFCFCDSXF
                    # To 2025-03-20
                    "date": (
                        datetime.strptime(
                            instrument_run_id.split("_")[0],
                            "%y%m%d"
                        ).strftime(
                            "%Y-%m-%d"
                        )
                    ),
                    # Generate readset
                    # But consider that the read2FileUri may not exist
                    "readSet": dict(filter(
                        lambda kv: kv[1] is not None,
                        {
                            "r1": {
                                "s3Uri": index_row_iter_[1]["read1FileUri"],
                            },
                            "r2": {
                                "s3Uri": index_row_iter_[1].get("read2FileUri", None),
                            },
                            "compressionFormat": "GZIP" if index_row_iter_[1]["read1FileUri"].endswith(
                                ".gz") else "ORA",
                        }.items()
                    )),
                    "readCount": index_row_iter_[1]["readCount"],
                    "baseCountEst": (index_row_iter_[1]["readCount"] * index_row_iter_[1]["cycleCount"]),
                    "isValid": True,
                },
                merged_df.iterrows()
            ))
        }
    )


def fastq_list_row_exists(
        library_id: str,
        lane: int,
        instrument_run_id: str,
) -> bool:
    """
    Return true if the fastq list row exists
    otherwise false
    :param library_id:
    :param lane:
    :param instrument_run_id:
    :return:
    """


def get_ssm_client() -> 'SSMClient':
    return boto3.client('ssm')


def create_gspread_pandas_dir() -> Path:
    """
    Get the gspread pandas creds directory
    :return:
    """

    # Create the directory
    gspread_pandas_creds_dir = TemporaryDirectory()

    return Path(gspread_pandas_creds_dir.name)


def get_google_secret_contents() -> str:
    ssm_client: SSMClient = get_ssm_client()

    return ssm_client.get_parameter(
        Name=environ[GDRIVE_AUTH_JSON_SSM_PARAMETER_PATH_ENV_VAR],
        WithDecryption=True
    ).get("Parameter").get("Value")


def download_google_secret_json_to_gspread_pandas_dir(gspread_pandas_dir: Path):
    secret_contents: str = get_google_secret_contents()

    if not gspread_pandas_dir.is_dir():
        gspread_pandas_dir.mkdir(parents=True, exist_ok=True)

    with open(gspread_pandas_dir / "google_secret.json", "w") as g_secret_h:
        g_secret_h.write(secret_contents)


def set_google_secrets():
    if environ.get("GSPREAD_PANDAS_CONFIG_DIR", None) is not None:
        return

    # Add in the secret and set the env var
    gspread_pandas_dir = create_gspread_pandas_dir()

    download_google_secret_json_to_gspread_pandas_dir(gspread_pandas_dir)

    environ["GSPREAD_PANDAS_CONFIG_DIR"] = str(gspread_pandas_dir)


def get_tracking_sheet_id() -> str:
    """
    Get the sheet id for glims
    """
    ssm_client: SSMClient = get_ssm_client()

    return ssm_client.get_parameter(
        Name=environ[METADATA_TRACKING_SHEET_ID_SSM_PARAMETER_PATH_ENV_VAR],
        WithDecryption=True
    ).get("Parameter").get("Value")


def get_metadata_sheet_for_library_year(year: int) -> pd.DataFrame:
    metadata_sheet_df: pd.DataFrame = Spread(
        spread=get_tracking_sheet_id(),
        sheet=f"{year}"
    ).sheet_to_df(index=0)

    return metadata_sheet_df.replace("", pd.NA)


def get_year_from_library_id(library_id: str):
    """
    Regex to get the year from the library id
    L(?:PRJ)?\d{2}(?:\d{5})?
    :param library_id:
    :return:
    """
    library_regex_obj = GET_YEAR_FROM_LIBRARY_ID_REGEX.match(
        library_id
    )

    if library_regex_obj is None:
        raise ValueError(
            f"Could not get year from library id: {library_id}"
        )

    # Get the year from the library id
    year = library_regex_obj.group(1)

    return datetime.strptime(year, "%y").year


def has_existing_fastq_set(
        library_id: Optional[str] = None,
        instrument_run_id: Optional[str] = None,
        is_current_fastq_set: Optional[bool] = None
) -> bool:
    """
    Check if there already exists a current fastq set for this library id.
    If this is true then we may have a topup or a rerun. In order to
    find this out, we will need to pull down the lab-metadata sheet.
    :param library_id:
    :param instrument_run_id:
    :param is_current_fastq_set:
    :return:
    """
    return (
        True
        if len(get_fastq_sets(
            **dict(filter(
                lambda kv: kv[1] is not None,
                {
                    "library": library_id,
                    "instrumentRunId": instrument_run_id,
                    "currentFastqSet": json.dumps(is_current_fastq_set) if is_current_fastq_set else None,
                }.items()
            ))
        )) > 0
        else False
    )


def is_topup(
        library_id: str,
) -> bool:
    library_id_list = get_metadata_sheet_for_library_year(
        get_year_from_library_id(library_id)
    )['LibraryID'].dropna().unique().tolist()

    if f"{library_id}_topup" in library_id_list:
        return True
    return False


def is_rerun(
        library_id: str,
) -> bool:
    library_id_list=get_metadata_sheet_for_library_year(
        get_year_from_library_id(library_id)
    )['LibraryID'].dropna().unique().tolist()

    if f"{library_id}_rerun" in library_id_list:
        return True
    return False

def append_to_existing_fastq_set(
    library_id: str,
    instrument_run_id: str,
    bclconvert_data_df: pd.DataFrame,
    filenames_df: pd.DataFrame,
    demux_stats_df: pd.DataFrame,
) -> FastqSet:
    """
    Append fastqs to the existing fastq set

    1. First we must allow additional fastqs to the existing fastq set

    2. Then we create the new fastq list rows for the new fastqs

    3. Then we link each of the fastqs to the fastq set

    4. And then we disable adding additional fastqs to the existing fastq set
    :return:
    """

    # Get the existing fastq set
    fastq_set = get_fastq_sets(
        library=library_id,
        currentFastqSet=json.dumps(True),
    )

    # Check we have one and only one fastq set
    if len(fastq_set) != 1:
        raise ValueError(f"Expected one and only one fastq set for this library id {library_id}")

    # Get the existing fastq set
    fastq_set = fastq_set[0]

    # Allow additional fastqs to the existing fastq set
    allow_additional_fastqs_to_fastq_set(fastq_set_id=fastq_set['id'])

    # Create the new fastq list row objects from the inputs
    new_fastq_fastq_list_rows = generate_fastq_list_row_list_from_inputs(
        instrument_run_id=instrument_run_id,
        bclconvert_data_df=bclconvert_data_df,
        filenames_df=filenames_df,
        demux_stats_df=demux_stats_df,
    )

    # Link each of the fastqs to the fastq set
    for new_fastq_list_row in new_fastq_fastq_list_rows:
        link_fastq_list_row_to_fastq_set(
            fastq_set_id=fastq_set['id'],
            fastq_id=new_fastq_list_row['id']
        )

    # Disable adding additional fastqs to the existing fastq set
    disallow_additional_fastqs_to_fastq_set(fastq_set_id=fastq_set['id'])

    return fastq_set



def replace_current_fastq_set(
        library_id: str,
        instrument_run_id: str,
        bclconvert_data_df: pd.DataFrame,
        filenames_df: pd.DataFrame,
        demux_stats_df: pd.DataFrame,
):
    """
    Rerun the fastq set -
    We will supercede the existing fastq set with the new one

    First we need to:

    1. Get the existing fastq set and set currentFastqSet to false
    2. Create the new fastq set object from the inputs
    :return:
    """

    # Get the existing fastq set
    fastq_set = get_fastq_sets(
        library=library_id,
        currentFastqSet=json.dumps(True)
    )

    # Check we have one and only one fastq set
    if len(fastq_set) != 1:
        raise ValueError(f"Expected one and only one fastq set for this library id {library_id}")

    # Get the existing fastq set
    fastq_set = fastq_set[0]

    # Set the existing fastq set to not current
    _ = set_is_not_current_fastq_set(fastq_set['id'])

    # Create the new fastq set object from the inputs
    return generate_fastq_set_from_inputs(
        instrument_run_id=instrument_run_id,
        bclconvert_data_df=bclconvert_data_df,
        filenames_df=filenames_df,
        demux_stats_df=demux_stats_df,
    )


def generate_fastq_set_from_inputs(
        instrument_run_id: str,
        bclconvert_data_df: pd.DataFrame,
        filenames_df: pd.DataFrame,
        demux_stats_df: pd.DataFrame,
) -> dict:
    """
    Create the fastq set object from the input dataframes
    """
    merged_df = merge_dataframes(bclconvert_data_df, filenames_df, demux_stats_df)

    # Create the fastq set object
    fastq_set = create_fastq_set_from_df(
        instrument_run_id=instrument_run_id,
        merged_df=merged_df,
    )

    return fastq_set


def handler(event, context):
    """
    Given the
    :param event:
    :param context:
    :return:
    """
    # Get the inputs from the event
    instrument_run_id = event["instrumentRunId"]
    bclconvert_data_df = pd.DataFrame(event["sampleBclConvertData"])
    filenames_df = pd.DataFrame(event["sampleFileNames"])
    demux_stats_df = pd.DataFrame(event["sampleDemuxStats"])

    # Check if has existing fastq set
    # If has existing fastq set for this instrument run id, we just return
    # Chances are we've already created the fastq set
    library_id = bclconvert_data_df["libraryId"].unique().item()
    if has_existing_fastq_set(
            library_id=library_id,
            instrument_run_id=instrument_run_id,
    ):
        return get_fastq_sets(
            library=library_id,
            instrumentRunId=instrument_run_id,
        )

    # If has existing fastq set for this library id
    # But not on this run
    if has_existing_fastq_set(
            library_id=library_id,
            is_current_fastq_set=True
    ):
        # Check if topup or rerun
        # Now we pull in the metadata tracking sheet
        set_google_secrets()

        if is_topup(library_id):
            return append_to_existing_fastq_set(
                library_id=library_id,
                instrument_run_id=instrument_run_id,
                bclconvert_data_df=bclconvert_data_df,
                filenames_df=filenames_df,
                demux_stats_df=demux_stats_df,
            )

        if is_rerun(library_id):
            return replace_current_fastq_set(
                library_id=library_id,
                instrument_run_id=instrument_run_id,
                bclconvert_data_df=bclconvert_data_df,
                filenames_df=filenames_df,
                demux_stats_df=demux_stats_df,
            )

        raise ValueError(
            f"Found library {library_id} on run {instrument_run_id} but already exists in the fastq manager with another instrument run id"
            f"and could not find a topup or rerun in the metadata tracking sheet"
        )

    # Otherwise
    # Generate the fastq set object
    return generate_fastq_set_from_inputs(
        instrument_run_id=instrument_run_id,
        bclconvert_data_df=bclconvert_data_df,
        filenames_df=filenames_df,
        demux_stats_df=demux_stats_df,
    )


# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(json.dumps(
#         handler(
#             {
#                 "sampleId": "L2401544",
#                 "sampleDemuxStats": [
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 2,
#                         "readCount": 56913395
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 3,
#                         "readCount": 62441372
#                     }
#                 ],
#                 "sampleFileNames": [
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 2,
#                         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
#                         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora"
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 3,
#                         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
#                         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora"
#                     }
#                 ],
#                 "sampleBclConvertData": [
#                     {
#                         "libraryId": "L2401544",
#                         "index": "CAAGCTAG+CGCTATGT",
#                         "lane": 2,
#                         "cycleCount": 302
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "index": "CAAGCTAG+CGCTATGT",
#                         "lane": 3,
#                         "cycleCount": 302
#                     }
#                 ],
#                 "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "id": "fqs.01JQ3B08TYFDPM8Z6ZXDFN9C2X",
#     #     "library": {
#     #         "orcabusId": "lib.01JBB5Y3QGZSGF74W6CTV0JJ16",
#     #         "libraryId": "L2401544"
#     #     },
#     #     "fastqSet": [
#     #         {
#     #             "id": "fqr.01JQ3B08PZYHF9JJVKE3SMQQFP",
#     #             "fastqSetId": "fqs.01JQ3B08TYFDPM8Z6ZXDFN9C2X",
#     #             "index": "CAAGCTAG+CGCTATGT",
#     #             "lane": 2,
#     #             "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#     #             "library": {
#     #                 "orcabusId": "lib.01JBB5Y3QGZSGF74W6CTV0JJ16",
#     #                 "libraryId": "L2401544"
#     #             },
#     #             "platform": "Illumina",
#     #             "center": "UMCCR",
#     #             "date": "2024-10-24T00:00:00",
#     #             "readSet": {
#     #                 "r1": {
#     #                     "ingestId": "0195c5fb-018d-7003-863c-67214a67fef7",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "r2": {
#     #                     "ingestId": "0195c5fb-0628-7873-86d0-194d0a3bd32b",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "compressionFormat": "ORA"
#     #             },
#     #             "qc": null,
#     #             "ntsm": null,
#     #             "readCount": 56913395,
#     #             "baseCountEst": 113826790,
#     #             "isValid": true
#     #         },
#     #         {
#     #             "id": "fqr.01JQ3B08RWZMTBC4M4DVMJY2R4",
#     #             "fastqSetId": "fqs.01JQ3B08TYFDPM8Z6ZXDFN9C2X",
#     #             "index": "CAAGCTAG+CGCTATGT",
#     #             "lane": 3,
#     #             "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#     #             "library": {
#     #                 "orcabusId": "lib.01JBB5Y3QGZSGF74W6CTV0JJ16",
#     #                 "libraryId": "L2401544"
#     #             },
#     #             "platform": "Illumina",
#     #             "center": "UMCCR",
#     #             "date": "2024-10-24T00:00:00",
#     #             "readSet": {
#     #                 "r1": {
#     #                     "ingestId": "0195c5fb-2d9b-7640-8120-3afc60bfeb9e",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "r2": {
#     #                     "ingestId": "0195c5fb-3072-7010-ab86-aae7adb1ac4e",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "compressionFormat": "ORA"
#     #             },
#     #             "qc": null,
#     #             "ntsm": null,
#     #             "readCount": 62441372,
#     #             "baseCountEst": 124882744,
#     #             "isValid": true
#     #         }
#     #     ],
#     #     "allowAdditionalFastq": false,
#     #     "isCurrentFastqSet": true
#     # }


# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(json.dumps(
#         handler(
#             {
#                 "sampleId": "L2401544",
#                 "sampleDemuxStats": [
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 2,
#                         "readCount": 56913395
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 3,
#                         "readCount": 62441372
#                     }
#                 ],
#                 "sampleFileNames": [
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 2,
#                         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
#                         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora"
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 3,
#                         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
#                         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora"
#                     }
#                 ],
#                 "sampleBclConvertData": [
#                     {
#                         "libraryId": "L2401544",
#                         "index": "CAAGCTAG+CGCTATGT",
#                         "lane": 2,
#                         "cycleCount": 302
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "index": "CAAGCTAG+CGCTATGT",
#                         "lane": 3,
#                         "cycleCount": 302
#                     }
#                 ],
#                 "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#             },
#             None
#         ),
#         indent=4
#     ))



# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(json.dumps(
#         handler(
#             {
#                 "sampleId": "L2401544",
#                 "sampleDemuxStats": [
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 2,
#                         "readCount": 56913395
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 3,
#                         "readCount": 62441372
#                     }
#                 ],
#                 "sampleFileNames": [
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 2,
#                         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
#                         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora"
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "lane": 3,
#                         "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
#                         "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora"
#                     }
#                 ],
#                 "sampleBclConvertData": [
#                     {
#                         "libraryId": "L2401544",
#                         "index": "CAAGCTAG+CGCTATGT",
#                         "lane": 2,
#                         "cycleCount": 302
#                     },
#                     {
#                         "libraryId": "L2401544",
#                         "index": "CAAGCTAG+CGCTATGT",
#                         "lane": 3,
#                         "cycleCount": 302
#                     }
#                 ],
#                 "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "id": "fqs.01JQ3B08TYFDPM8Z6ZXDFN9C2X",
#     #     "library": {
#     #         "orcabusId": "lib.01JBB5Y3QGZSGF74W6CTV0JJ16",
#     #         "libraryId": "L2401544"
#     #     },
#     #     "fastqSet": [
#     #         {
#     #             "id": "fqr.01JQ3B08PZYHF9JJVKE3SMQQFP",
#     #             "fastqSetId": "fqs.01JQ3B08TYFDPM8Z6ZXDFN9C2X",
#     #             "index": "CAAGCTAG+CGCTATGT",
#     #             "lane": 2,
#     #             "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#     #             "library": {
#     #                 "orcabusId": "lib.01JBB5Y3QGZSGF74W6CTV0JJ16",
#     #                 "libraryId": "L2401544"
#     #             },
#     #             "platform": "Illumina",
#     #             "center": "UMCCR",
#     #             "date": "2024-10-24T00:00:00",
#     #             "readSet": {
#     #                 "r1": {
#     #                     "ingestId": "0195c5fb-018d-7003-863c-67214a67fef7",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R1_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "r2": {
#     #                     "ingestId": "0195c5fb-0628-7873-86d0-194d0a3bd32b",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_2/L2401544/L2401544_S12_L002_R2_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "compressionFormat": "ORA"
#     #             },
#     #             "qc": null,
#     #             "ntsm": null,
#     #             "readCount": 56913395,
#     #             "baseCountEst": 113826790,
#     #             "isValid": true
#     #         },
#     #         {
#     #             "id": "fqr.01JQ3B08RWZMTBC4M4DVMJY2R4",
#     #             "fastqSetId": "fqs.01JQ3B08TYFDPM8Z6ZXDFN9C2X",
#     #             "index": "CAAGCTAG+CGCTATGT",
#     #             "lane": 3,
#     #             "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#     #             "library": {
#     #                 "orcabusId": "lib.01JBB5Y3QGZSGF74W6CTV0JJ16",
#     #                 "libraryId": "L2401544"
#     #             },
#     #             "platform": "Illumina",
#     #             "center": "UMCCR",
#     #             "date": "2024-10-24T00:00:00",
#     #             "readSet": {
#     #                 "r1": {
#     #                     "ingestId": "0195c5fb-2d9b-7640-8120-3afc60bfeb9e",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R1_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "r2": {
#     #                     "ingestId": "0195c5fb-3072-7010-ab86-aae7adb1ac4e",
#     #                     "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_3/L2401544/L2401544_S12_L003_R2_001.fastq.ora",
#     #                     "storageClass": "Standard",
#     #                     "gzipCompressionSizeInBytes": null,
#     #                     "rawMd5sum": null
#     #                 },
#     #                 "compressionFormat": "ORA"
#     #             },
#     #             "qc": null,
#     #             "ntsm": null,
#     #             "readCount": 62441372,
#     #             "baseCountEst": 124882744,
#     #             "isValid": true
#     #         }
#     #     ],
#     #     "allowAdditionalFastq": false,
#     #     "isCurrentFastqSet": true
#     # }
