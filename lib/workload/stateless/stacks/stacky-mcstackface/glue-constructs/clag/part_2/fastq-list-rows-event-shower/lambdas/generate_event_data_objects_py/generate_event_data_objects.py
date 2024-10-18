#!/usr/bin/env python3

"""
Given a set of fastq list rows, generate a set of event maps for each fastq file,
along with a create event shower as well
"""

# Imports
from typing import Dict


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

    :param num_readcount_obj_list:
    :param qc_obj_list:
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

    # Generate the fastq list row events
    fastq_list_row_event_data_list = list(
        map(
            lambda fastq_list_row_iter_: generate_fastq_list_row_event(
                fastq_list_row_iter_,
                next(
                    filter(
                        lambda library_iter_: library_iter_['libraryId'] == fastq_list_row_iter_['rgsm'],
                        library_obj_list
                    )
                ),
                instrument_run_id
            ),
            fastq_list_rows
        )
    )

    # Generate the start and complete shower event data
    start_fastq_list_row_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    complete_fastq_list_row_shower_event_data = {
        "instrumentRunId": instrument_run_id,
    }

    project_event_data_list = []
    for project_obj_iter_ in project_obj_list:
        library_objects_in_project = list(
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
                                project_obj_iter_.get("librarySet")
                            )
                        )
                    ),
                    library_obj_list
                )
            )
        )

        # Get project object
        project_obj = dict(
            filter(
                lambda kv: not kv[0] == 'librarySet',
                project_obj_iter_.items()
            )
        )

        project_event_data_list.append(
            {
                "event_data": {
                    "instrumentRunId": instrument_run_id,
                    "project": project_obj,
                    "libraryFastqSet": library_objects_in_project
                }
            }
        )

    # Return the event data
    return {
        "start_fastq_list_row_shower_event_data": start_fastq_list_row_shower_event_data,
        "project_event_data_list": project_event_data_list,
        "fastq_list_rows_event_data_list": fastq_list_row_event_data_list,
        "complete_fastq_list_row_shower_event_data": complete_fastq_list_row_shower_event_data,
    }


# Test the function
# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "library_objs": [
#                         {
#                             "orcabusId": "lib.01J8ES4MPZ5B201R50K42XXM4M",
#                             "libraryId": "L2400102",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "borderline",
#                             "type": "WGS",
#                             "assay": "ctTSO",
#                             "coverage": 50
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#                             "libraryId": "L2400159",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XQG3MPBW94TTVT4STVG",
#                             "libraryId": "L2400160",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#                             "libraryId": "L2400161",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#                             "libraryId": "L2400162",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#                             "libraryId": "L2400163",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#                             "libraryId": "L2400164",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#                             "libraryId": "L2400165",
#                             "phenotype": "tumor",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 38.6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4Y5D52202JVBXHJ9Q9WF",
#                             "libraryId": "L2400166",
#                             "phenotype": "negative-control",
#                             "workflow": "manual",
#                             "quality": "good",
#                             "type": "ctDNA",
#                             "assay": "ctTSOv2",
#                             "coverage": 0.1
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#                             "libraryId": "L2400191",
#                             "phenotype": "normal",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#                             "libraryId": "L2400195",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#                             "libraryId": "L2400196",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ",
#                             "libraryId": "L2400197",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9",
#                             "libraryId": "L2400198",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 80
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED",
#                             "libraryId": "L2400231",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "poor",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 100
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0",
#                             "libraryId": "L2400238",
#                             "phenotype": "normal",
#                             "workflow": "clinical",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#                             "libraryId": "L2400239",
#                             "phenotype": "normal",
#                             "workflow": "clinical",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 40
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83",
#                             "libraryId": "L2400240",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "poor",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 100
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#                             "libraryId": "L2400241",
#                             "phenotype": "negative-control",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 0.1
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#                             "libraryId": "L2400242",
#                             "phenotype": "normal",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WGS",
#                             "assay": "TsqNano",
#                             "coverage": 15
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52XYMVGRB1Q458THNG4T",
#                             "libraryId": "L2400249",
#                             "phenotype": "tumor",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 1
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#                             "libraryId": "L2400250",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES530H895X4WA3NQ6CY2QV",
#                             "libraryId": "L2400251",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#                             "libraryId": "L2400252",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#                             "libraryId": "L2400253",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES534XGBFYDVYV8ZG6SYS0",
#                             "libraryId": "L2400254",
#                             "phenotype": "tumor",
#                             "workflow": "research",
#                             "quality": "borderline",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#                             "libraryId": "L2400255",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "very-poor",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES537S0W1AX9PQPST13GM9",
#                             "libraryId": "L2400256",
#                             "phenotype": "tumor",
#                             "workflow": "clinical",
#                             "quality": "very-poor",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 6
#                         },
#                         {
#                             "orcabusId": "lib.01J8ES5395KETT9T2NJSVNDKNP",
#                             "libraryId": "L2400257",
#                             "phenotype": "negative-control",
#                             "workflow": "control",
#                             "quality": "good",
#                             "type": "WTS",
#                             "assay": "NebRNA",
#                             "coverage": 0.1
#                         }
#                     ],
#                     "project_objs": [
#                         {
#                             "name": None,
#                             "description": None,
#                             "librarySet": [
#                                 "lib.01J8ES4MPZ5B201R50K42XXM4M"
#                             ],
#                             "projectId": "PO",
#                             "orcabusId": "prj.01J8ES4EBXK08WDWB97BSCX1C9"
#                         },
#                         {
#                             "name": None,
#                             "description": None,
#                             "librarySet": [
#                                 "lib.01J8ES51V0RSVT6C7WQR72QQED",
#                                 "lib.01J8ES52889Q8826P5SH9HDPP0",
#                                 "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#                                 "lib.01J8ES52C3N585BGGY4VNXHC83",
#                                 "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#                                 "lib.01J8ES537S0W1AX9PQPST13GM9"
#                             ],
#                             "projectId": "CUP",
#                             "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3"
#                         },
#                         {
#                             "name": None,
#                             "description": None,
#                             "librarySet": [
#                                 "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#                                 "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#                                 "lib.01J8ES52XYMVGRB1Q458THNG4T",
#                                 "lib.01J8ES5395KETT9T2NJSVNDKNP"
#                             ],
#                             "projectId": "Control",
#                             "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8"
#                         },
#                         {
#                             "name": None,
#                             "description": None,
#                             "librarySet": [
#                                 "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#                                 "lib.01J8ES530H895X4WA3NQ6CY2QV",
#                                 "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#                                 "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#                                 "lib.01J8ES534XGBFYDVYV8ZG6SYS0"
#                             ],
#                             "projectId": "BPOP-retro",
#                             "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX"
#                         },
#                         {
#                             "name": None,
#                             "description": None,
#                             "librarySet": [
#                                 "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#                                 "lib.01J8ES4XQG3MPBW94TTVT4STVG",
#                                 "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#                                 "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#                                 "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#                                 "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#                                 "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#                                 "lib.01J8ES4Y5D52202JVBXHJ9Q9WF"
#                             ],
#                             "projectId": "Testing",
#                             "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1"
#                         },
#                         {
#                             "name": None,
#                             "description": None,
#                             "librarySet": [
#                                 "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#                                 "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#                                 "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#                                 "lib.01J8ES4ZST489C712CG3R9NQSQ",
#                                 "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9"
#                             ],
#                             "projectId": "CAVATAK",
#                             "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B"
#                         }
#                     ],
#                     "fastq_list_rows": [
#                         {
#                             "rgid": "GAATTCGT.TTATGAGT.1.240229_A00130_0288_BH5HM2DSXC.L2400102",
#                             "rgsm": "L2400102",
#                             "rglb": "L2400102",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GAGAATGGTT.TTGCTGCCGA.1.240229_A00130_0288_BH5HM2DSXC.L2400159",
#                             "rgsm": "L2400159",
#                             "rglb": "L2400159",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "AGAGGCAACC.CCATCATTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400160",
#                             "rgsm": "L2400160",
#                             "rglb": "L2400160",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "CCATCATTAG.AGAGGCAACC.1.240229_A00130_0288_BH5HM2DSXC.L2400161",
#                             "rgsm": "L2400161",
#                             "rglb": "L2400161",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GATAGGCCGA.GCCATGTGCG.1.240229_A00130_0288_BH5HM2DSXC.L2400162",
#                             "rgsm": "L2400162",
#                             "rglb": "L2400162",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ATGGTTGACT.AGGACAGGCC.1.240229_A00130_0288_BH5HM2DSXC.L2400163",
#                             "rgsm": "L2400163",
#                             "rglb": "L2400163",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "TATTGCGCTC.CCTAACACAG.1.240229_A00130_0288_BH5HM2DSXC.L2400164",
#                             "rgsm": "L2400164",
#                             "rglb": "L2400164",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "TTCTACATAC.TTACAGTTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400166",
#                             "rgsm": "L2400166",
#                             "rglb": "L2400166",
#                             "lane": 1,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ATGAGGCC.CAATTAAC.2.240229_A00130_0288_BH5HM2DSXC.L2400195",
#                             "rgsm": "L2400195",
#                             "rglb": "L2400195",
#                             "lane": 2,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ACTAAGAT.CCGCGGTT.2.240229_A00130_0288_BH5HM2DSXC.L2400196",
#                             "rgsm": "L2400196",
#                             "rglb": "L2400196",
#                             "lane": 2,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GTCGGAGC.TTATAACC.2.240229_A00130_0288_BH5HM2DSXC.L2400197",
#                             "rgsm": "L2400197",
#                             "rglb": "L2400197",
#                             "lane": 2,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "TCGTAGTG.CCAAGTCT.2.240229_A00130_0288_BH5HM2DSXC.L2400231",
#                             "rgsm": "L2400231",
#                             "rglb": "L2400231",
#                             "lane": 2,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GGAGCGTC.GCACGGAC.2.240229_A00130_0288_BH5HM2DSXC.L2400238",
#                             "rgsm": "L2400238",
#                             "rglb": "L2400238",
#                             "lane": 2,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ATGGCATG.GGTACCTT.2.240229_A00130_0288_BH5HM2DSXC.L2400239",
#                             "rgsm": "L2400239",
#                             "rglb": "L2400239",
#                             "lane": 2,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GCAATGCA.AACGTTCC.2.240229_A00130_0288_BH5HM2DSXC.L2400240",
#                             "rgsm": "L2400240",
#                             "rglb": "L2400240",
#                             "lane": 2,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ATGAGGCC.CAATTAAC.3.240229_A00130_0288_BH5HM2DSXC.L2400195",
#                             "rgsm": "L2400195",
#                             "rglb": "L2400195",
#                             "lane": 3,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ACTAAGAT.CCGCGGTT.3.240229_A00130_0288_BH5HM2DSXC.L2400196",
#                             "rgsm": "L2400196",
#                             "rglb": "L2400196",
#                             "lane": 3,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GTCGGAGC.TTATAACC.3.240229_A00130_0288_BH5HM2DSXC.L2400197",
#                             "rgsm": "L2400197",
#                             "rglb": "L2400197",
#                             "lane": 3,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "TCGTAGTG.CCAAGTCT.3.240229_A00130_0288_BH5HM2DSXC.L2400231",
#                             "rgsm": "L2400231",
#                             "rglb": "L2400231",
#                             "lane": 3,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GGAGCGTC.GCACGGAC.3.240229_A00130_0288_BH5HM2DSXC.L2400238",
#                             "rgsm": "L2400238",
#                             "rglb": "L2400238",
#                             "lane": 3,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ATGGCATG.GGTACCTT.3.240229_A00130_0288_BH5HM2DSXC.L2400239",
#                             "rgsm": "L2400239",
#                             "rglb": "L2400239",
#                             "lane": 3,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GCAATGCA.AACGTTCC.3.240229_A00130_0288_BH5HM2DSXC.L2400240",
#                             "rgsm": "L2400240",
#                             "rglb": "L2400240",
#                             "lane": 3,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ACGCCTTGTT.ACGTTCCTTA.4.240229_A00130_0288_BH5HM2DSXC.L2400165",
#                             "rgsm": "L2400165",
#                             "rglb": "L2400165",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GCACGGAC.TGCGAGAC.4.240229_A00130_0288_BH5HM2DSXC.L2400191",
#                             "rgsm": "L2400191",
#                             "rglb": "L2400191",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GTCGGAGC.TTATAACC.4.240229_A00130_0288_BH5HM2DSXC.L2400197",
#                             "rgsm": "L2400197",
#                             "rglb": "L2400197",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "CTTGGTAT.GGACTTGG.4.240229_A00130_0288_BH5HM2DSXC.L2400198",
#                             "rgsm": "L2400198",
#                             "rglb": "L2400198",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GTTCCAAT.GCAGAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400241",
#                             "rgsm": "L2400241",
#                             "rglb": "L2400241",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "ACCTTGGC.ATGAGGCC.4.240229_A00130_0288_BH5HM2DSXC.L2400242",
#                             "rgsm": "L2400242",
#                             "rglb": "L2400242",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "AGTTTCGA.CCTACGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400249",
#                             "rgsm": "L2400249",
#                             "rglb": "L2400249",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GAACCTCT.GTCTGCGC.4.240229_A00130_0288_BH5HM2DSXC.L2400250",
#                             "rgsm": "L2400250",
#                             "rglb": "L2400250",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GCCCAGTG.CCGCAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400251",
#                             "rgsm": "L2400251",
#                             "rglb": "L2400251",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "TGACAGCT.CCCGTAGG.4.240229_A00130_0288_BH5HM2DSXC.L2400252",
#                             "rgsm": "L2400252",
#                             "rglb": "L2400252",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "CATCACCC.ATATAGCA.4.240229_A00130_0288_BH5HM2DSXC.L2400253",
#                             "rgsm": "L2400253",
#                             "rglb": "L2400253",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254",
#                             "rgsm": "L2400254",
#                             "rglb": "L2400254",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GATCCGGG.AAGCAGGT.4.240229_A00130_0288_BH5HM2DSXC.L2400255",
#                             "rgsm": "L2400255",
#                             "rglb": "L2400255",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "AACACCTG.CGCATGGG.4.240229_A00130_0288_BH5HM2DSXC.L2400256",
#                             "rgsm": "L2400256",
#                             "rglb": "L2400256",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#                         },
#                         {
#                             "rgid": "GTGACGTT.TCCCAGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400257",
#                             "rgsm": "L2400257",
#                             "rglb": "L2400257",
#                             "lane": 4,
#                             "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#                             "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#                         }
#                     ],
#                     "instrument_run_id": "240229_A00130_0288_BH5HM2DSXC"
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
#     #         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#     #     },
#     #     "project_event_data_list": [
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "project": {
#     #                     "name": null,
#     #                     "description": null,
#     #                     "projectId": "PO",
#     #                     "orcabusId": "prj.01J8ES4EBXK08WDWB97BSCX1C9"
#     #                 },
#     #                 "libraryFastqSet": [
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4MPZ5B201R50K42XXM4M",
#     #                             "libraryId": "L2400102"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GAATTCGT.TTATGAGT.1.240229_A00130_0288_BH5HM2DSXC.L2400102",
#     #                                 "rgsm": "L2400102",
#     #                                 "rglb": "L2400102",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "project": {
#     #                     "name": null,
#     #                     "description": null,
#     #                     "projectId": "CUP",
#     #                     "orcabusId": "prj.01J8ES4EZAA5YMHX82664GJQB3"
#     #                 },
#     #                 "libraryFastqSet": [
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED",
#     #                             "libraryId": "L2400231"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TCGTAGTG.CCAAGTCT.2.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                                 "rgsm": "L2400231",
#     #                                 "rglb": "L2400231",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "TCGTAGTG.CCAAGTCT.3.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                                 "rgsm": "L2400231",
#     #                                 "rglb": "L2400231",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0",
#     #                             "libraryId": "L2400238"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GGAGCGTC.GCACGGAC.2.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                                 "rgsm": "L2400238",
#     #                                 "rglb": "L2400238",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GGAGCGTC.GCACGGAC.3.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                                 "rgsm": "L2400238",
#     #                                 "rglb": "L2400238",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8",
#     #                             "libraryId": "L2400239"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ATGGCATG.GGTACCTT.2.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                                 "rgsm": "L2400239",
#     #                                 "rglb": "L2400239",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "ATGGCATG.GGTACCTT.3.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                                 "rgsm": "L2400239",
#     #                                 "rglb": "L2400239",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83",
#     #                             "libraryId": "L2400240"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GCAATGCA.AACGTTCC.2.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                                 "rgsm": "L2400240",
#     #                                 "rglb": "L2400240",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GCAATGCA.AACGTTCC.3.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                                 "rgsm": "L2400240",
#     #                                 "rglb": "L2400240",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES536AB5A5PBJ8S45SZP7Q",
#     #                             "libraryId": "L2400255"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GATCCGGG.AAGCAGGT.4.240229_A00130_0288_BH5HM2DSXC.L2400255",
#     #                                 "rgsm": "L2400255",
#     #                                 "rglb": "L2400255",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES537S0W1AX9PQPST13GM9",
#     #                             "libraryId": "L2400256"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "AACACCTG.CGCATGGG.4.240229_A00130_0288_BH5HM2DSXC.L2400256",
#     #                                 "rgsm": "L2400256",
#     #                                 "rglb": "L2400256",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "project": {
#     #                     "name": null,
#     #                     "description": null,
#     #                     "projectId": "Control",
#     #                     "orcabusId": "prj.01J8ES4FC6DVW20AR33FBX2SA8"
#     #                 },
#     #                 "libraryFastqSet": [
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES52DHAPZM6FZ0VZK89PRT",
#     #                             "libraryId": "L2400241"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GTTCCAAT.GCAGAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400241",
#     #                                 "rgsm": "L2400241",
#     #                                 "rglb": "L2400241",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES52F2ZHRXQY1AT1N1F81F",
#     #                             "libraryId": "L2400242"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ACCTTGGC.ATGAGGCC.4.240229_A00130_0288_BH5HM2DSXC.L2400242",
#     #                                 "rgsm": "L2400242",
#     #                                 "rglb": "L2400242",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES52XYMVGRB1Q458THNG4T",
#     #                             "libraryId": "L2400249"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "AGTTTCGA.CCTACGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400249",
#     #                                 "rgsm": "L2400249",
#     #                                 "rglb": "L2400249",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES5395KETT9T2NJSVNDKNP",
#     #                             "libraryId": "L2400257"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GTGACGTT.TCCCAGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400257",
#     #                                 "rgsm": "L2400257",
#     #                                 "rglb": "L2400257",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "project": {
#     #                     "name": null,
#     #                     "description": null,
#     #                     "projectId": "BPOP-retro",
#     #                     "orcabusId": "prj.01J8ES4FH3XMPZQNDJ9J000BXX"
#     #                 },
#     #                 "libraryFastqSet": [
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10",
#     #                             "libraryId": "L2400250"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GAACCTCT.GTCTGCGC.4.240229_A00130_0288_BH5HM2DSXC.L2400250",
#     #                                 "rgsm": "L2400250",
#     #                                 "rglb": "L2400250",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES530H895X4WA3NQ6CY2QV",
#     #                             "libraryId": "L2400251"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GCCCAGTG.CCGCAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400251",
#     #                                 "rgsm": "L2400251",
#     #                                 "rglb": "L2400251",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES5320EWBNNYDGXF2SYJBD",
#     #                             "libraryId": "L2400252"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TGACAGCT.CCCGTAGG.4.240229_A00130_0288_BH5HM2DSXC.L2400252",
#     #                                 "rgsm": "L2400252",
#     #                                 "rglb": "L2400252",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES533DJZZNPP9MXYR5TRC0",
#     #                             "libraryId": "L2400253"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CATCACCC.ATATAGCA.4.240229_A00130_0288_BH5HM2DSXC.L2400253",
#     #                                 "rgsm": "L2400253",
#     #                                 "rglb": "L2400253",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES534XGBFYDVYV8ZG6SYS0",
#     #                             "libraryId": "L2400254"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254",
#     #                                 "rgsm": "L2400254",
#     #                                 "rglb": "L2400254",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "project": {
#     #                     "name": null,
#     #                     "description": null,
#     #                     "projectId": "Testing",
#     #                     "orcabusId": "prj.01J8ES4XMWD0DH7MDRNER5TZS1"
#     #                 },
#     #                 "libraryFastqSet": [
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4XNYFP38JMDV7GMV0V3V",
#     #                             "libraryId": "L2400159"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GAGAATGGTT.TTGCTGCCGA.1.240229_A00130_0288_BH5HM2DSXC.L2400159",
#     #                                 "rgsm": "L2400159",
#     #                                 "rglb": "L2400159",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4XQG3MPBW94TTVT4STVG",
#     #                             "libraryId": "L2400160"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "AGAGGCAACC.CCATCATTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400160",
#     #                                 "rgsm": "L2400160",
#     #                                 "rglb": "L2400160",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4XSS97XNRS8DH0B1RJRG",
#     #                             "libraryId": "L2400161"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CCATCATTAG.AGAGGCAACC.1.240229_A00130_0288_BH5HM2DSXC.L2400161",
#     #                                 "rgsm": "L2400161",
#     #                                 "rglb": "L2400161",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4XXF6NMEJMM5M4GWS6KH",
#     #                             "libraryId": "L2400162"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GATAGGCCGA.GCCATGTGCG.1.240229_A00130_0288_BH5HM2DSXC.L2400162",
#     #                                 "rgsm": "L2400162",
#     #                                 "rglb": "L2400162",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X",
#     #                             "libraryId": "L2400163"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ATGGTTGACT.AGGACAGGCC.1.240229_A00130_0288_BH5HM2DSXC.L2400163",
#     #                                 "rgsm": "L2400163",
#     #                                 "rglb": "L2400163",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP",
#     #                             "libraryId": "L2400164"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TATTGCGCTC.CCTAACACAG.1.240229_A00130_0288_BH5HM2DSXC.L2400164",
#     #                                 "rgsm": "L2400164",
#     #                                 "rglb": "L2400164",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1",
#     #                             "libraryId": "L2400165"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ACGCCTTGTT.ACGTTCCTTA.4.240229_A00130_0288_BH5HM2DSXC.L2400165",
#     #                                 "rgsm": "L2400165",
#     #                                 "rglb": "L2400165",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4Y5D52202JVBXHJ9Q9WF",
#     #                             "libraryId": "L2400166"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "TTCTACATAC.TTACAGTTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400166",
#     #                                 "rgsm": "L2400166",
#     #                                 "rglb": "L2400166",
#     #                                 "lane": 1,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         },
#     #         {
#     #             "event_data": {
#     #                 "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #                 "project": {
#     #                     "name": null,
#     #                     "description": null,
#     #                     "projectId": "CAVATAK",
#     #                     "orcabusId": "prj.01J8ES4ZAWHH3FKYA2CFHSMZ4B"
#     #                 },
#     #                 "libraryFastqSet": [
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW",
#     #                             "libraryId": "L2400191"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GCACGGAC.TGCGAGAC.4.240229_A00130_0288_BH5HM2DSXC.L2400191",
#     #                                 "rgsm": "L2400191",
#     #                                 "rglb": "L2400191",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6",
#     #                             "libraryId": "L2400195"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ATGAGGCC.CAATTAAC.2.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                                 "rgsm": "L2400195",
#     #                                 "rglb": "L2400195",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "ATGAGGCC.CAATTAAC.3.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                                 "rgsm": "L2400195",
#     #                                 "rglb": "L2400195",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK",
#     #                             "libraryId": "L2400196"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "ACTAAGAT.CCGCGGTT.2.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                                 "rgsm": "L2400196",
#     #                                 "rglb": "L2400196",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "ACTAAGAT.CCGCGGTT.3.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                                 "rgsm": "L2400196",
#     #                                 "rglb": "L2400196",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ",
#     #                             "libraryId": "L2400197"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "GTCGGAGC.TTATAACC.2.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                                 "rgsm": "L2400197",
#     #                                 "rglb": "L2400197",
#     #                                 "lane": 2,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GTCGGAGC.TTATAACC.3.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                                 "rgsm": "L2400197",
#     #                                 "rglb": "L2400197",
#     #                                 "lane": 3,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#     #                             },
#     #                             {
#     #                                 "rgid": "GTCGGAGC.TTATAACC.4.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                                 "rgsm": "L2400197",
#     #                                 "rglb": "L2400197",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     },
#     #                     {
#     #                         "library": {
#     #                             "orcabusId": "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9",
#     #                             "libraryId": "L2400198"
#     #                         },
#     #                         "fastqPairs": [
#     #                             {
#     #                                 "rgid": "CTTGGTAT.GGACTTGG.4.240229_A00130_0288_BH5HM2DSXC.L2400198",
#     #                                 "rgsm": "L2400198",
#     #                                 "rglb": "L2400198",
#     #                                 "lane": 4,
#     #                                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#     #                                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#     #                             }
#     #                         ]
#     #                     }
#     #                 ]
#     #             }
#     #         }
#     #     ],
#     #     "fastq_list_rows_event_data_list": [
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400102",
#     #                 "orcabusId": "lib.01J8ES4MPZ5B201R50K42XXM4M"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GAATTCGT.TTATGAGT.1.240229_A00130_0288_BH5HM2DSXC.L2400102",
#     #                 "rgsm": "L2400102",
#     #                 "rglb": "L2400102",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400102/L2400102_S1_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400159",
#     #                 "orcabusId": "lib.01J8ES4XNYFP38JMDV7GMV0V3V"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GAGAATGGTT.TTGCTGCCGA.1.240229_A00130_0288_BH5HM2DSXC.L2400159",
#     #                 "rgsm": "L2400159",
#     #                 "rglb": "L2400159",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400159/L2400159_S2_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400159/L2400159_S2_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400160",
#     #                 "orcabusId": "lib.01J8ES4XQG3MPBW94TTVT4STVG"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "AGAGGCAACC.CCATCATTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400160",
#     #                 "rgsm": "L2400160",
#     #                 "rglb": "L2400160",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400161",
#     #                 "orcabusId": "lib.01J8ES4XSS97XNRS8DH0B1RJRG"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "CCATCATTAG.AGAGGCAACC.1.240229_A00130_0288_BH5HM2DSXC.L2400161",
#     #                 "rgsm": "L2400161",
#     #                 "rglb": "L2400161",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400161/L2400161_S4_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400161/L2400161_S4_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400162",
#     #                 "orcabusId": "lib.01J8ES4XXF6NMEJMM5M4GWS6KH"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GATAGGCCGA.GCCATGTGCG.1.240229_A00130_0288_BH5HM2DSXC.L2400162",
#     #                 "rgsm": "L2400162",
#     #                 "rglb": "L2400162",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400162/L2400162_S5_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400162/L2400162_S5_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400163",
#     #                 "orcabusId": "lib.01J8ES4XZD7T2VRPVQ1GSVZ11X"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ATGGTTGACT.AGGACAGGCC.1.240229_A00130_0288_BH5HM2DSXC.L2400163",
#     #                 "rgsm": "L2400163",
#     #                 "rglb": "L2400163",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400163/L2400163_S6_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400163/L2400163_S6_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400164",
#     #                 "orcabusId": "lib.01J8ES4Y1AKAHYD9EW0TW4FBCP"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "TATTGCGCTC.CCTAACACAG.1.240229_A00130_0288_BH5HM2DSXC.L2400164",
#     #                 "rgsm": "L2400164",
#     #                 "rglb": "L2400164",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400164/L2400164_S7_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400164/L2400164_S7_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400166",
#     #                 "orcabusId": "lib.01J8ES4Y5D52202JVBXHJ9Q9WF"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "TTCTACATAC.TTACAGTTAG.1.240229_A00130_0288_BH5HM2DSXC.L2400166",
#     #                 "rgsm": "L2400166",
#     #                 "rglb": "L2400166",
#     #                 "lane": 1,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400166/L2400166_S8_L001_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_1/L2400166/L2400166_S8_L001_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400195",
#     #                 "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ATGAGGCC.CAATTAAC.2.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                 "rgsm": "L2400195",
#     #                 "rglb": "L2400195",
#     #                 "lane": 2,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400195/L2400195_S9_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400195/L2400195_S9_L002_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400196",
#     #                 "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ACTAAGAT.CCGCGGTT.2.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                 "rgsm": "L2400196",
#     #                 "rglb": "L2400196",
#     #                 "lane": 2,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400196/L2400196_S10_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400196/L2400196_S10_L002_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400197",
#     #                 "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GTCGGAGC.TTATAACC.2.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                 "rgsm": "L2400197",
#     #                 "rglb": "L2400197",
#     #                 "lane": 2,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400197/L2400197_S11_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400197/L2400197_S11_L002_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400231",
#     #                 "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "TCGTAGTG.CCAAGTCT.2.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                 "rgsm": "L2400231",
#     #                 "rglb": "L2400231",
#     #                 "lane": 2,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400238",
#     #                 "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GGAGCGTC.GCACGGAC.2.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                 "rgsm": "L2400238",
#     #                 "rglb": "L2400238",
#     #                 "lane": 2,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400239",
#     #                 "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ATGGCATG.GGTACCTT.2.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                 "rgsm": "L2400239",
#     #                 "rglb": "L2400239",
#     #                 "lane": 2,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400239/L2400239_S14_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400239/L2400239_S14_L002_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400240",
#     #                 "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GCAATGCA.AACGTTCC.2.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                 "rgsm": "L2400240",
#     #                 "rglb": "L2400240",
#     #                 "lane": 2,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400240/L2400240_S15_L002_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_2/L2400240/L2400240_S15_L002_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400195",
#     #                 "orcabusId": "lib.01J8ES4ZMY0G1H9MDN7K2TH9Y6"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ATGAGGCC.CAATTAAC.3.240229_A00130_0288_BH5HM2DSXC.L2400195",
#     #                 "rgsm": "L2400195",
#     #                 "rglb": "L2400195",
#     #                 "lane": 3,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400195/L2400195_S9_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400195/L2400195_S9_L003_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400196",
#     #                 "orcabusId": "lib.01J8ES4ZP88X2E17X5X1FRMTPK"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ACTAAGAT.CCGCGGTT.3.240229_A00130_0288_BH5HM2DSXC.L2400196",
#     #                 "rgsm": "L2400196",
#     #                 "rglb": "L2400196",
#     #                 "lane": 3,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400196/L2400196_S10_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400196/L2400196_S10_L003_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400197",
#     #                 "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GTCGGAGC.TTATAACC.3.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                 "rgsm": "L2400197",
#     #                 "rglb": "L2400197",
#     #                 "lane": 3,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400197/L2400197_S11_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400197/L2400197_S11_L003_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400231",
#     #                 "orcabusId": "lib.01J8ES51V0RSVT6C7WQR72QQED"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "TCGTAGTG.CCAAGTCT.3.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #                 "rgsm": "L2400231",
#     #                 "rglb": "L2400231",
#     #                 "lane": 3,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400238",
#     #                 "orcabusId": "lib.01J8ES52889Q8826P5SH9HDPP0"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GGAGCGTC.GCACGGAC.3.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #                 "rgsm": "L2400238",
#     #                 "rglb": "L2400238",
#     #                 "lane": 3,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400239",
#     #                 "orcabusId": "lib.01J8ES52ANMRT3B7Y96T1Y3RY8"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ATGGCATG.GGTACCTT.3.240229_A00130_0288_BH5HM2DSXC.L2400239",
#     #                 "rgsm": "L2400239",
#     #                 "rglb": "L2400239",
#     #                 "lane": 3,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400239/L2400239_S14_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400239/L2400239_S14_L003_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400240",
#     #                 "orcabusId": "lib.01J8ES52C3N585BGGY4VNXHC83"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GCAATGCA.AACGTTCC.3.240229_A00130_0288_BH5HM2DSXC.L2400240",
#     #                 "rgsm": "L2400240",
#     #                 "rglb": "L2400240",
#     #                 "lane": 3,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400240/L2400240_S15_L003_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_3/L2400240/L2400240_S15_L003_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400165",
#     #                 "orcabusId": "lib.01J8ES4Y3ZKRX3C5JAHA5NBXV1"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ACGCCTTGTT.ACGTTCCTTA.4.240229_A00130_0288_BH5HM2DSXC.L2400165",
#     #                 "rgsm": "L2400165",
#     #                 "rglb": "L2400165",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400165/L2400165_S16_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400165/L2400165_S16_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400191",
#     #                 "orcabusId": "lib.01J8ES4ZDRQAP2BN3SDYYV5PKW"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GCACGGAC.TGCGAGAC.4.240229_A00130_0288_BH5HM2DSXC.L2400191",
#     #                 "rgsm": "L2400191",
#     #                 "rglb": "L2400191",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400191/L2400191_S17_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400191/L2400191_S17_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400197",
#     #                 "orcabusId": "lib.01J8ES4ZST489C712CG3R9NQSQ"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GTCGGAGC.TTATAACC.4.240229_A00130_0288_BH5HM2DSXC.L2400197",
#     #                 "rgsm": "L2400197",
#     #                 "rglb": "L2400197",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400197/L2400197_S11_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400197/L2400197_S11_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400198",
#     #                 "orcabusId": "lib.01J8ES4ZVWA2CGBHJVKAS3Y0G9"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "CTTGGTAT.GGACTTGG.4.240229_A00130_0288_BH5HM2DSXC.L2400198",
#     #                 "rgsm": "L2400198",
#     #                 "rglb": "L2400198",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400198/L2400198_S18_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400198/L2400198_S18_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400241",
#     #                 "orcabusId": "lib.01J8ES52DHAPZM6FZ0VZK89PRT"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GTTCCAAT.GCAGAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400241",
#     #                 "rgsm": "L2400241",
#     #                 "rglb": "L2400241",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400241/L2400241_S19_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400241/L2400241_S19_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400242",
#     #                 "orcabusId": "lib.01J8ES52F2ZHRXQY1AT1N1F81F"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "ACCTTGGC.ATGAGGCC.4.240229_A00130_0288_BH5HM2DSXC.L2400242",
#     #                 "rgsm": "L2400242",
#     #                 "rglb": "L2400242",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400242/L2400242_S20_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400242/L2400242_S20_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400249",
#     #                 "orcabusId": "lib.01J8ES52XYMVGRB1Q458THNG4T"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "AGTTTCGA.CCTACGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400249",
#     #                 "rgsm": "L2400249",
#     #                 "rglb": "L2400249",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400249/L2400249_S21_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400249/L2400249_S21_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400250",
#     #                 "orcabusId": "lib.01J8ES52Z2KTVVKZ2ZGVQ6YC10"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GAACCTCT.GTCTGCGC.4.240229_A00130_0288_BH5HM2DSXC.L2400250",
#     #                 "rgsm": "L2400250",
#     #                 "rglb": "L2400250",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400250/L2400250_S22_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400250/L2400250_S22_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400251",
#     #                 "orcabusId": "lib.01J8ES530H895X4WA3NQ6CY2QV"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GCCCAGTG.CCGCAATT.4.240229_A00130_0288_BH5HM2DSXC.L2400251",
#     #                 "rgsm": "L2400251",
#     #                 "rglb": "L2400251",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400252",
#     #                 "orcabusId": "lib.01J8ES5320EWBNNYDGXF2SYJBD"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "TGACAGCT.CCCGTAGG.4.240229_A00130_0288_BH5HM2DSXC.L2400252",
#     #                 "rgsm": "L2400252",
#     #                 "rglb": "L2400252",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400252/L2400252_S24_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400252/L2400252_S24_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400253",
#     #                 "orcabusId": "lib.01J8ES533DJZZNPP9MXYR5TRC0"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "CATCACCC.ATATAGCA.4.240229_A00130_0288_BH5HM2DSXC.L2400253",
#     #                 "rgsm": "L2400253",
#     #                 "rglb": "L2400253",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400253/L2400253_S25_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400253/L2400253_S25_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400254",
#     #                 "orcabusId": "lib.01J8ES534XGBFYDVYV8ZG6SYS0"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "CTGGAGTA.GTTCGGTT.4.240229_A00130_0288_BH5HM2DSXC.L2400254",
#     #                 "rgsm": "L2400254",
#     #                 "rglb": "L2400254",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400254/L2400254_S26_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400255",
#     #                 "orcabusId": "lib.01J8ES536AB5A5PBJ8S45SZP7Q"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GATCCGGG.AAGCAGGT.4.240229_A00130_0288_BH5HM2DSXC.L2400255",
#     #                 "rgsm": "L2400255",
#     #                 "rglb": "L2400255",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400255/L2400255_S27_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400255/L2400255_S27_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400256",
#     #                 "orcabusId": "lib.01J8ES537S0W1AX9PQPST13GM9"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "AACACCTG.CGCATGGG.4.240229_A00130_0288_BH5HM2DSXC.L2400256",
#     #                 "rgsm": "L2400256",
#     #                 "rglb": "L2400256",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz"
#     #             }
#     #         },
#     #         {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "library": {
#     #                 "libraryId": "L2400257",
#     #                 "orcabusId": "lib.01J8ES5395KETT9T2NJSVNDKNP"
#     #             },
#     #             "fastqListRow": {
#     #                 "rgid": "GTGACGTT.TCCCAGAT.4.240229_A00130_0288_BH5HM2DSXC.L2400257",
#     #                 "rgsm": "L2400257",
#     #                 "rglb": "L2400257",
#     #                 "lane": 4,
#     #                 "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R1_001.fastq.gz",
#     #                 "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202409108ed29dcc/Samples/Lane_4/L2400257/L2400257_S29_L004_R2_001.fastq.gz"
#     #             }
#     #         }
#     #     ],
#     #     "complete_fastq_list_row_shower_event_data": {
#     #         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#     #     }
#     # }