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

# Imports
import pandas as pd
from datetime import datetime

# Layer imports
from fastq_tools import create_fastq_set_object, FastqSet

# Globals
DEFAULT_PLATFORM = "Illumina"
DEFAULT_CENTER = "UMCCR"


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

    # Generate the fastq set object
    fastq_set = generate_fastq_set_from_inputs(
        instrument_run_id=instrument_run_id,
        bclconvert_data_df=bclconvert_data_df,
        filenames_df=filenames_df,
        demux_stats_df=demux_stats_df,
    )

    return fastq_set


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
