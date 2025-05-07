#!/usr/bin/env python3

"""
Generate event data objects

Given an instrument run id, samplesheet, library_obj_list, sample_obj_list, subject_obj_list,
Generate the events for

* Start of the SampleSheet Shower
* Library Event Data Objects (library id, plus event data)
* End of the SampleSheet Shower
"""
# Imports
import gzip
import json
from base64 import b64decode
from typing import Dict, List, Union
from metadata_tools import get_library_from_library_id, Library


# Functions
def decompress_dict(input_compressed_b64gz_str: str) -> Union[Dict, List]:
    """
    Given a base64 encoded string, decompress and return the original dictionary
    Args:
        input_compressed_b64gz_str:

    Returns: decompressed dictionary or list
    """

    # Decompress
    return json.loads(
        gzip.decompress(
            b64decode(input_compressed_b64gz_str.encode('utf-8'))
        )
    )


def get_library_bclconvert_rows(library_obj: Dict, bclconvert_data: List[Dict]) -> List[Dict]:
    """
    Get library bclconvert rows
    :param library_obj:
    :param bclconvert_data:
    :return:
    """
    return list(
        filter(
            lambda bclconvert_row: bclconvert_row.get("sample_id") == library_obj.get("libraryId"),
            bclconvert_data
        )
    )


def generate_library_event_data_object_from_library(
        library_obj: Library,
        instrument_run_id: str,
        bclconvert_rows: List[Dict]
) -> Dict:
    """
    Generate library event data object from library specimen and subject
    :param library_obj:
    :param instrument_run_id:
    :param bclconvert_rows:
    :return:
    """

    library_event_obj = {
        "orcabusId": library_obj.get("orcabusId"),
        "libraryId": library_obj.get("libraryId"),
        "phenotype": library_obj.get("phenotype", None),
        "workflow": library_obj.get("workflow", None),
        "quality": library_obj.get("quality", None),
        "type": library_obj.get("type", None),
        "assay": library_obj.get("assay", None),
        "coverage": library_obj.get("coverage", None),
    }

    # Trim library event object to non-null values
    library_event_obj = dict(
        filter(
            lambda kv: kv[1] is not None,
            library_event_obj.items()
        )
    )

    # Filter re-key bclconvert data rows
    bclconvert_data_rows_event_obj = []
    fastq_list_row_ids = []

    for bclconvert_row_obj in bclconvert_rows:
        bclconvert_row_event_obj = {
            "sampleId": bclconvert_row_obj.get("sample_id"),
            "index": bclconvert_row_obj.get("index"),
            "index2": bclconvert_row_obj.get("index2", None),
            "lane": bclconvert_row_obj.get("lane"),
            "overrideCycles": bclconvert_row_obj.get("override_cycles", None)
        }

        # Trim bclconvert row event object to non-null values
        bclconvert_row_event_obj = dict(
            filter(
                lambda kv: kv[1] is not None,
                bclconvert_row_event_obj.items()
            )
        )

        bclconvert_data_rows_event_obj.append(bclconvert_row_event_obj)

        fastq_list_row_ids.append(
            {
                "fastqListRowRgid": '.'.join(
                    map(
                        str,
                        filter(
                            lambda x: x is not None,
                            [
                                bclconvert_row_obj.get("index"),
                                bclconvert_row_obj.get("index2", None),
                                bclconvert_row_obj.get("lane"),
                                instrument_run_id,
                                bclconvert_row_obj.get("sample_id"),
                            ]
                        )
                    )
                )
            }
        )

    return {
        "instrumentRunId": instrument_run_id,
        "library": library_event_obj,
        "sample": library_obj.get("sample", None),
        "subject": library_obj.get("subject", None),
        "projectSet": library_obj.get("projectSet", None),
        "bclconvertDataRows": bclconvert_data_rows_event_obj,
        "fastqListRows": fastq_list_row_ids,
    }


def handler(event, context):
    """
    Generate the event objects

    :param event:
    :param context:
    :return:
    """

    # Get the library id
    library_id = event['libraryId']
    bclconvert_library_data = list(filter(
        lambda bclconvert_data_row_iter_: bclconvert_data_row_iter_['sample_id'] == library_id,
        decompress_dict(event['samplesheetB64gz'])['bclconvert_data']
    ))
    instrument_run_id = event['instrumentRunId']

    # Get the library object list
    library_obj = get_library_from_library_id(
        library_id=library_id
    )

    event_data = generate_library_event_data_object_from_library(
        library_obj=library_obj,
        instrument_run_id=instrument_run_id,
        bclconvert_rows=bclconvert_library_data
    )


    return {
        "libraryObj": library_obj,
        "eventDataObj": event_data
    }


# if __name__ == "__main__":
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#
#     print(json.dumps(
#         handler(
#             {
#                 "libraryId": "L2500485",
#                 "samplesheetB64gz": 'H4sIAHS9FmgC/61XUW/aMBD+K1X2OipiDCTsyfODNWnry/wyTdPJJKaLGhIaQjtU9b/vHIhL3JFFilVUgWO+7+78ne/jJfitVaqrYHXzEmyyXMOmrLaqhidd7bOywHXy8SaoDgUUaqvxYyD3jwWZTymJgHxTRzIPcENW7OvqsNVFDfVx1+y7K5/Ud/0YvJrvI8m+4TDvIITkmOTarITz8PwciLuaFan+c7k5sosXeyNDsE7ypCww6Br2uq6z4v5EV+JSlaX6bXvwA8E/fYnMy7w10e/LTf2sKn2RdUBvye0ycLBTVSt8+PMlyFVhsjRh7tV2h4XLUvO1r1iaKV0ugzZUsyikkFwIZhdJs8oFZ0xwQ/JfwKgDKCXniCm7gAjGJONyEGDcAUQ4yRnnToQCw8PQhwBG027KHOGYEE6EUmDOUgwCDDuATGLCgr2rIUM4zgYBzpxD4Vgs5qTMTCXEsEOJnBpi8bFgzqEgWJN0B5D4lg3xLRviWzbEt2yIb9kQ37IhvmUz8x3hNUDqRIhVZO8AJUMiLgYBzrs6xDhQ2PK9sE3ogwAX3VMWRsCuDlkjJSkHATqtx4yA3U4RjZT4sBo6rYfZ4TE7EXIToivsK4Bxt1Oa3LBiTspGM0g0CNDpFGbuBiZcHXJDM6iGMenWUJi7wb2+jNzNddMBpL6FTX0Lm/oWNvUtbOpb2NS3sKlvYVPfwqZehP0L15O8PKRdL3qvC12pWqeXNnN6i3+B/cJzWT1s8vLZPMoSZT9Dk9KFE91lO51nTdDBoSpWWb7Ff4latQ9W6008W8+TzSRZk+WEphs1iehCT1SSLvR6GoUqUR8+Jzk/Iz5RdNUnx3uK5c3sXrUqebauVHW0vw3aZ9BaF7Bu5WL3rtI7eMjqy58Ud6ooT0dx1cZcIYugtTVgncwosriHLIbW8oB1OWPITvbn32TRFFo7BNYBjSILe8hCaK0SWHc0imzWQzaD9i4He32PIqM9ZBTaex7s1T6KbN5DNod2BoC99keRLXrIFtDOB7AjYRRZT1NH2NTn2QF2XIwi62nqCJv6PFfAjpJRZD1NHWFTnz04WNs9hizuaep4Cu2AAzvTRpH1NHUcQjv8wM67UWSkh4xAOxjBzsJBZL9e/wIcbs84hxIAAA==',  # pragma: allowlist secret
#                 "instrumentRunId": "250502_A00130_0367_AHFH2WDSXF"
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "libraryObj": {
#     #         "orcabusId": "lib.01JSXK18EADPG4E8D6VCM5S33H",
#     #         "projectSet": [
#     #             {
#     #                 "orcabusId": "prj.01JBMVXFEY2HEBA1MDDBVKKX4Z",
#     #                 "projectId": "BPOP",
#     #                 "name": null,
#     #                 "description": null
#     #             }
#     #         ],
#     #         "sample": {
#     #             "orcabusId": "smp.01JSXK18DSRTPP1ESSRH6P5G0C",
#     #             "sampleId": "MDX250174",
#     #             "externalSampleId": "ELIBRO220425-G",
#     #             "source": "blood"
#     #         },
#     #         "subject": {
#     #             "orcabusId": "sbj.01JSXK18D017763NV216Y5TES1",
#     #             "individualSet": [
#     #                 {
#     #                     "orcabusId": "idv.01JSXK18CSXADBDR2H8EQ6BVMR",
#     #                     "individualId": "SBJ06567",
#     #                     "source": "lab"
#     #                 }
#     #             ],
#     #             "subjectId": "9319747"
#     #         },
#     #         "libraryId": "L2500485",
#     #         "phenotype": "normal",
#     #         "workflow": "clinical",
#     #         "quality": "good",
#     #         "type": "WGS",
#     #         "assay": "TsqNano",
#     #         "coverage": 40.0,
#     #         "overrideCycles": "Y151;I8;I8;Y151"
#     #     },
#     #     "eventDataObj": {
#     #         "instrumentRunId": "250502_A00130_0367_AHFH2WDSXF",
#     #         "library": {
#     #             "orcabusId": "lib.01JSXK18EADPG4E8D6VCM5S33H",
#     #             "libraryId": "L2500485",
#     #             "phenotype": "normal",
#     #             "workflow": "clinical",
#     #             "quality": "good",
#     #             "type": "WGS",
#     #             "assay": "TsqNano",
#     #             "coverage": 40.0
#     #         },
#     #         "sample": {
#     #             "orcabusId": "smp.01JSXK18DSRTPP1ESSRH6P5G0C",
#     #             "sampleId": "MDX250174",
#     #             "externalSampleId": "ELIBRO220425-G",
#     #             "source": "blood"
#     #         },
#     #         "subject": {
#     #             "orcabusId": "sbj.01JSXK18D017763NV216Y5TES1",
#     #             "individualSet": [
#     #                 {
#     #                     "orcabusId": "idv.01JSXK18CSXADBDR2H8EQ6BVMR",
#     #                     "individualId": "SBJ06567",
#     #                     "source": "lab"
#     #                 }
#     #             ],
#     #             "subjectId": "9319747"
#     #         },
#     #         "projectSet": [
#     #             {
#     #                 "orcabusId": "prj.01JBMVXFEY2HEBA1MDDBVKKX4Z",
#     #                 "projectId": "BPOP",
#     #                 "name": null,
#     #                 "description": null
#     #             }
#     #         ],
#     #         "bclconvertDataRows": [
#     #             {
#     #                 "sampleId": "L2500485",
#     #                 "index": "TGGCCGGT",
#     #                 "index2": "GCGCTCTA",
#     #                 "lane": 3
#     #             },
#     #             {
#     #                 "sampleId": "L2500485",
#     #                 "index": "TGGCCGGT",
#     #                 "index2": "GCGCTCTA",
#     #                 "lane": 4
#     #             }
#     #         ],
#     #         "fastqListRows": [
#     #             {
#     #                 "fastqListRowRgid": "TGGCCGGT.GCGCTCTA.3.250502_A00130_0367_AHFH2WDSXF.L2500485"
#     #             },
#     #             {
#     #                 "fastqListRowRgid": "TGGCCGGT.GCGCTCTA.4.250502_A00130_0367_AHFH2WDSXF.L2500485"
#     #             }
#     #         ]
#     #     }
#     # }