#!/usr/bin/env python3

"""
Given a set of fastq list rows, generate a set of event maps for each fastq file,
along with a create event shower as well

Write these to the dynamodb database, rather than as an output as we cannot control how large the number
of samples will be and this may overload the size.
"""
# Imports
import typing
from typing import Dict, List
from os import environ
import boto3
import json

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

# Table name
DYNAMODB_TABLE_NAME_ENV_VAR = "INSTRUMENT_RUN_TABLE_NAME"

# Table partitions
FASTQ_LIST_ROW_EVENT_OBJ_PARTITION_ENV_VAR = "FASTQ_LIST_ROW_EVENT_OBJ_TABLE_PARTITION_NAME"
PROJECT_EVENT_OBJ_PARTITION_ENV_VAR = "PROJECT_EVENT_OBJ_TABLE_PARTITION_NAME"


def get_dynamodb_db_client() -> 'DynamoDBClient':
    return boto3.client('dynamodb')


def get_table_name() -> str:
    return environ.get(DYNAMODB_TABLE_NAME_ENV_VAR)


def put_item(
        id: str,
        id_type: str,  # This is the database partition
        event_data: Dict,
):
    get_dynamodb_db_client().put_item(
        TableName=get_table_name(),
        Item={
            'id': {'S': id},
            'id_type': {'S': id_type},
            'event_data': {'S': json.dumps(event_data, separators=(',', ':'))},
        }
    )


def pascal_to_camel_case(pascal_str: str) -> str:
    """
    Convert a string from PascalCase to camelCase
    :param pascal_str:
    :return:
    """
    # If the string is empty, return an empty string
    if not pascal_str:
        return ""

    # If the string is only one character long, return the string
    if len(pascal_str) < 2:
        return pascal_str.lower()

    # Return the string as camel case
    return pascal_str[0].lower() + pascal_str[1:]


def generate_fastq_list_row_event(fastq_list_row: Dict, library: Dict, instrument_run_id: str) -> Dict:
    """
    Generate the fastq list row event
    :param library:
    :param fastq_list_row:
    :param instrument_run_id:
    :return:
    """
    return {
        "instrumentRunId": instrument_run_id,
        "library": {
            "libraryId": library.get("libraryId"),
            "orcabusId": library.get("orcabusId")
        },
        "fastqListRow": fastq_list_row,
    }


def get_fastq_list_row_dynamodb_put_objects(
        instrument_run_id: str,
        library_obj_list: List[Dict[str, str]],
        fastq_list_rows: List[Dict[str, str]]
):
    return list(
        map(
            lambda fastq_list_row_iter_: {
                "id": f"{fastq_list_row_iter_['rgid']}__{instrument_run_id}",
                "id_type": environ.get(FASTQ_LIST_ROW_EVENT_OBJ_PARTITION_ENV_VAR),
                "event_data": generate_fastq_list_row_event(
                    fastq_list_row_iter_,
                    next(
                        filter(
                            lambda library_iter_: library_iter_['libraryId'] == fastq_list_row_iter_['rgsm'],
                            library_obj_list
                        )
                    ),
                    instrument_run_id
                )
            },
            fastq_list_rows
        )
    )


def get_libraries_in_project(
        project_obj: Dict[str, str],
        fastq_list_row_event_data_list: List[Dict[str, str]],
        library_obj_list: List[Dict[str, str]]
):
    return list(
        map(
            lambda library_obj_iter: {
                "library": {
                    "orcabusId": library_obj_iter.get("orcabusId"),
                    "libraryId": library_obj_iter.get("libraryId"),
                },
                "fastqPairs": list(
                    map(
                        lambda fastq_list_row_event_data_iter: (
                            fastq_list_row_event_data_iter.get("fastqListRow")
                        ),
                        filter(
                            lambda fastq_list_row_event_data_iter: (
                                    fastq_list_row_event_data_iter.get("library").get("libraryId") ==
                                    library_obj_iter.get("libraryId")
                            ),
                            fastq_list_row_event_data_list
                        )
                    )
                )
            },
            filter(
                lambda library_obj_iter_: (
                    any(
                        map(
                            lambda project_obj_iter_: (
                                    library_obj_iter_.get("orcabusId") ==
                                    project_obj_iter_
                            ),
                            project_obj.get("librarySet")
                        )
                    )
                ),
                library_obj_list
            )
        )
    )


def get_project_dynamodb_put_objects(
        instrument_run_id: str,
        project_obj_list: List[Dict[str, str]],
        fastq_list_row_event_data_list: List[Dict[str, str]],
        library_obj_list: List[Dict[str, str]]
):
    return list(
        map(
            lambda project_obj_iter_: {
                "id": f"{project_obj_iter_.get('orcabusId')}__{instrument_run_id}",
                "id_type": environ.get(PROJECT_EVENT_OBJ_PARTITION_ENV_VAR),
                "event_data": {
                    "instrumentRunId": instrument_run_id,
                    "project": dict(
                        filter(
                            lambda kv: not kv[0] == 'librarySet',
                            project_obj_iter_.items()
                        )
                    ),
                    "libraryFastqSet": get_libraries_in_project(
                        project_obj=project_obj_iter_,
                        fastq_list_row_event_data_list=fastq_list_row_event_data_list,
                        library_obj_list=library_obj_list
                    )
                }
            },
            project_obj_list
        )
    )


def handler(event, context):
    """
    Given a set of fastq list rows (and instrument run id), generate a set of event maps for each fastq file.
    :param event:
    :param context:
    :return:
    """

    # Get the fastq list rows and instrument run id
    fastq_list_rows = event['fastq_list_rows']
    library_obj_list = event['library_objs']
    project_obj_list = event['project_objs']
    instrument_run_id = event['instrument_run_id']

    # Generate the start and complete shower event data
    # These are returned in the response
    start_fastq_list_row_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    complete_fastq_list_row_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    # Generate the fastq list row events
    # We place these into dynamodb since we have no control of the size
    # Of the data we need may be returning
    fastq_list_row_dynamodb_obj_list = get_fastq_list_row_dynamodb_put_objects(
        instrument_run_id=instrument_run_id,
        fastq_list_rows=fastq_list_rows,
        library_obj_list=library_obj_list
    )

    # Write fastq list row event details to database
    project_dynamodb_obj_list = get_project_dynamodb_put_objects(
        instrument_run_id=instrument_run_id,
        project_obj_list=project_obj_list,
        fastq_list_row_event_data_list=list(
            map(
                lambda fastq_list_row_dynamodb_iter_: fastq_list_row_dynamodb_iter_.get("event_data"),
                fastq_list_row_dynamodb_obj_list
            )
        ),
        library_obj_list=library_obj_list
    )

    # Write fastq list row event objs to database
    _ = list(
        map(
            lambda fastq_list_row_dynamodb_iter_: put_item(**fastq_list_row_dynamodb_iter_),
            fastq_list_row_dynamodb_obj_list
        )
    )

    # Write project event objs to database
    _ = list(
        map(
            lambda project_dynamodb_iter_: put_item(**project_dynamodb_iter_),
            project_dynamodb_obj_list
        )
    )

    # Return the event data
    return {
        "start_fastq_list_row_shower_event_data": start_fastq_list_row_shower_event_data,
        "complete_fastq_list_row_shower_event_data": complete_fastq_list_row_shower_event_data,
    }


# Test the function
# if __name__ == "__main__":
#     import json
#     environ["AWS_PROFILE"] = 'umccr-production'
#     environ["INSTRUMENT_RUN_TABLE_NAME"] = "stacky-instrument-run-table"
#     environ["FASTQ_LIST_ROW_EVENT_OBJ_TABLE_PARTITION_NAME"] = "fastq_list_row_event"
#     environ["PROJECT_EVENT_OBJ_TABLE_PARTITION_NAME"] = "project_event"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "library_objs": [
#                         {
#                             "orcabusId": "lib.01JBMVXZJ8NCWRG81HT6PGGY9A",
#                             "libraryId": "LPRJ241015",
#                             "workflow": "qc",
#                             "type": "BiModal",
#                             "assay": "BM-5L",
#                             "coverage": 60
#                         },
#                         ...
#                     ],
#                     "project_objs": [
#                         {
#                             "name": None,
#                             "description": None,
#                             "librarySet": [
#                                 "lib.01JBMTZJ78561JM9QF6NKTPM03",
#                                 "lib.01JBMTZMTW947JKQ6DV6JCZGYH",
#                                 "lib.01JBMV04AC83KWVGMV2AZHYA00",
#                                 "lib.01JBMV04KN763N47H52Q5QG2RB",
#                                 "lib.01JBMV04QXP5XZ9ZQCYDPNZ872",
#                                 "lib.01JBMV04TSSY28J55GSFHK95XF",
#                                 "lib.01JBMV0515911AYC0PGD20GJJK",
#                                 "lib.01JBMV0BH1NNB3TD8WX4CNR3JS",
#                                 "lib.01JBMV0BKV31SC02HX91VZ4SE6",
#                                 "lib.01JBMV0C9151207GKCMK7SP9QY",
#                                 "lib.01JBMV0CA4XNM65QRP8BW81X2E",
#                                 "lib.01JBMV22VWG42HJVG4MXTFM4E2",
#                                 "lib.01JBMV26C7P15437FKKZR26R3Z",
#                                 "lib.01JBMV26KERNPZ0X78FR0ZXZYK",
#                                 "lib.01JBMVGBDTGJ59Z4XBN9BT44KG",
#                                 "lib.01JBMVGBET032CHSM22VRET5CX",
#                                 "lib.01JBMVGBHTZ6EDRDFF1WDP31AK",
#                                 "lib.01JBMVGBKTNE562YM1JD6JHKPX",
#                                 "lib.01JBMVGCX2ZWFV8D4TGGKBN3H6",
#                                 "lib.01JBMVGD2XY32XM7B7SQKXM46X",
#                                 "lib.01JBMVGDCJTSZYXCWX3F8M6GSD",
#                                 "lib.01JBMVGDDEF5EDWWFXN1T5BV4T",
#                                 "lib.01JBMVGMX9YKS1Z5NMW1RY44ZM",
#                                 "lib.01JBMVGN0BZRDGH0FCYV44Y11A",
#                                 "lib.01JBMVGNNXP2VQDPVNJC1KYA5T",
#                                 "lib.01JBMVGNQQGXD3JCHCTG466BVN",
#                                 "lib.01JBMVGPF9BW9MCJ3741S78GA2",
#                                 "lib.01JBMVGPG95C36J7RM577KMWAN",
#                                 "lib.01JBMVGPKFZ62Y8AWT84KDNH13",
#                                 "lib.01JBMVGPPGZH0146F95QZF6ESX",
#                                 "lib.01JBMVHJJY3ZH7ZNH76S9KVKRM",
#                                 "lib.01JBMVHJM5Q6FMKPYH26TN0CR6",
#                                 "lib.01JBMVHJRC4FEHV70QQMDS2Y8C",
#                                 "lib.01JBMVHJWKHC2VNNM39E8NQ4Y6",
#                                 "lib.01JBMVHKYFFREY2DDEFHRYYD9D",
#                                 "lib.01JBMVHM1BAHTMV6W1C4G4Z718",
#                                 "lib.01JBMVHMD3AK91PRV4B72RCE75",
#                                 "lib.01JBMVHMW9H1GCXPEDFCF0HPJN",
#                                 "lib.01JBMVHMY76XD502E0TA4N9VXP",
#                                 "lib.01JBMVHN2846GR2FB8662TEYTE",
#                                 "lib.01JBMVHPZQ8QXEJ1MZWS3FMSXN",
#                                 "lib.01JBMVHQ2CZFXE9XVDBKVBSDYH",
#                                 "lib.01JBMVHQSQTCT2BM5TNVXAWPZD",
#                                 "lib.01JBMVHQTSYSSWB19XB0CQRQQB",
#                                 "lib.01JBMVYYDYWY6EC22QWJCNS05P",
#                                 "lib.01JBMVYYF0513DNBMWD9E76FNA",
#                                 "lib.01JBMVYYG0FETK52P956V65FAA",
#                                 "lib.01JBMVYYPG7PQ3DFZA3490YB5K",
#                                 "lib.01JBMW0AF20EACKCKPZ2KDDEVA",
#                                 "lib.01JBMW0AG2F271247S3FGFPPMD",
#                                 "lib.01JBMW0AY90EZASFKF5SQWTPYK",
#                                 "lib.01JBMW0AZCWJAAX4C33BY912EX",
#                                 "lib.01JBMW0B0GKXEDMF0ECJ54P1N7",
#                                 "lib.01JBMW0B5SMV496ZYX9G1DPDHE",
#                                 "lib.01JC0QB21QDVJYBSC38KB8A1W5",
#                                 "lib.01JC0QB260AH48ZMYZGD6YKXKA",
#                                 "lib.01JC0QB2KENB0Z3GA5QN9243KC",
#                                 "lib.01JC0QB2MG0N7P319FFA9K8DC2",
#                                 "lib.01JCG5QXMVVKZN9VDBFHY7PB7Y",
#                                 "lib.01JCG5QXP50C0J9HPWE3883ADC",
#                                 "lib.01JCG5QXRZWZ8A2HCJY00454NA",
#                                 "lib.01JCG5QXWPPWKQA2ZHBCHP1YQE",
#                                 "lib.01JCZM3FSACVYPVBD4AG94K4TE",
#                                 "lib.01JCZM3FVEN1HZYG58X5JB4YWH",
#                                 "lib.01JCZM3GA1VQXVHRZG14D53XKQ",
#                                 "lib.01JCZM3GCHRNYTJ5720HKMFP8R",
#                                 "lib.01JCZM3GEEV55D33Q68EJ86GQ7",
#                                 "lib.01JCZM3GYQFA1MJG9ZRS42SGPZ",
#                                 "lib.01JCZM3HEJHBC7Y2WY46HSVPK5",
#                                 "lib.01JCZM3HGP9E3GCF64FGNW09VD",
#                                 "lib.01JDPSP5XGVRH7X95FXVTVH4QF",
#                                 "lib.01JDPSP61V9YZAZM62FHAS87F9",
#                                 "lib.01JDPSP72WNMEEY6SHBSC9QV0N",
#                                 "lib.01JDPSP75G2W4KDPAECWT100CP",
#                                 "lib.01JE681VW076VYJZEQ4P5MVQES",
#                                 "lib.01JE681VXATSQ279T1SATDPAP3",
#                                 "lib.01JE681WGCCCE96HH3M2MC9PZ2",
#                                 "lib.01JE681WNV28G589BFFZJES33B",
#                                 "lib.01JER8VVQB4R6Q993EK85S79C8",
#                                 "lib.01JER8VVWQ8VWN56DQGR9R7CK0",
#                                 "lib.01JER8VW9E5KVH4ZB4E3TSC266",
#                                 "lib.01JER8VWBKJZKNAH5KERPQ0P55",
#                                 "lib.01JFA9M635CVWDC2FCX0QE340B",
#                                 "lib.01JFA9M65HCNHDJDYH63F6J9XX",
#                                 "lib.01JFA9M67XT8P4D1NM1S1YXKYQ",
#                                 "lib.01JFA9M6PD17DFECEHNKB3Z913",
#                                 "lib.01JFA9M7498FG6XJ8RFC65W9Z5",
#                                 "lib.01JFA9M7FJJD8F5J5SRGA1MKK5",
#                                 "lib.01JFCW0WTDX071Q8F98D19YYWM",
#                                 "lib.01JFFEDF0TT0CZQVCGHDYKRGC7",
#                                 "lib.01JGXSH42PVH0213YGY7K990KH",
#                                 "lib.01JGXSH44PYTTBJ14CSYSWQ94K",
#                                 "lib.01JHJCPCP55SA462E11Y3VQHQ8",
#                                 "lib.01JHJCPCQNTJRA8TM49XPV010E",
#                                 "lib.01JHJCPDBSXN6SAHYZ2M6M8DDP",
#                                 "lib.01JHJCPDEVPVHMEYJNY0MZ23QC",
#                                 "lib.01JJ1V2NA2C0TGWY00ANCPKX43",
#                                 "lib.01JJ1V2NVMVSDA2MPK92ZJQFE5",
#                                 "lib.01JJ1V2PBY00FF39QR518YCCFX",
#                                 "lib.01JJ1V2PDFGR2MXNKRF6TRBYTZ",
#                                 "lib.01JJ1V2PNRY848A2X73193QHSQ",
#                                 "lib.01JJ1V2PQEB8F8S6XXKCCTCKNA",
#                                 "lib.01JJPE8DJ9DXVX1DFN6JQT4G3T",
#                                 "lib.01JJPE8DM1SF57DVFPSJZ5EHK6",
#                                 "lib.01JJPE8DYC9YHA85MVBH71EZD5",
#                                 "lib.01JJPE8E2M15FGB8CXEF6J59VB"
#                             ],
#                             "projectId": "Control",
#                             "orcabusId": "prj.01JBMTCMSYMREZ7CYAT5SHTEJJ"
#                         },
#                         ...
#                     ],
#                     "fastq_list_rows": [
#                         {
#                             "rgid": "CGTACAGGAA.AGAGAACCTA.1.250131_A01052_0253_AH5FY3DSXF.LPRJ250045",
#                             "rgsm": "LPRJ250045",
#                             "rglb": "LPRJ250045",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/250131_A01052_0253_AH5FY3DSXF/202502018d52a554/Samples/Lane_1/LPRJ250045/LPRJ250045_S1_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/250131_A01052_0253_AH5FY3DSXF/202502018d52a554/Samples/Lane_1/LPRJ250045/LPRJ250045_S1_L001_R2_001.fastq.gz"
#                         }
#                         ...
#                     ],
#                     "instrument_run_id": "250131_A01052_0253_AH5FY3DSXF"
#                 },
#                 None
#             )
#             ,
#             indent=4
#         )
#     )
#
#     # {
#     #     "start_fastq_list_row_shower_event_data": {
#     #         "instrumentRunId": "250131_A01052_0253_AH5FY3DSXF"
#     #     },
#     #     "complete_fastq_list_row_shower_event_data": {
#     #         "instrumentRunId": "250131_A01052_0253_AH5FY3DSXF"
#     #     }
#     # }
