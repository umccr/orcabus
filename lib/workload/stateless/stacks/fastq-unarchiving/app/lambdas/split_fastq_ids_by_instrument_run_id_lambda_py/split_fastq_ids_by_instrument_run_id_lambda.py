#!/usr/bin/env python3

"""
Split fastq ids by instrument run id using fastq api

Given a list of fastq ids return a list of objects i.e

[
  "fqr1",
  "fqr2",
  "fqr3", 
  "fqr4"
]

Return a list of objects with the following structure

[
  {
    "instrumentRunId": "abcd1234",
    "fastqIds": ["fqr1", "fqr2"]
  }
]

"""
from typing import List, Dict, Union

from fastq_tools import get_fastq


def get_instrument_run_id_from_fastq_id(fastq_id: str) -> str:
    return get_fastq(fastq_id)['instrumentRunId']


def handler(event, context) -> Dict[str, List[Dict[str, Union[str, List[str]]]]]:
    """
    For each fastq id we get the instrument run id and then we group by instrument run id
    :param event:
    :param context:
    :return:
    """

    fastq_ids_list = event.get("fastqIdList", [])
    instrument_run_id_dict = {}

    # For each fastq
    for fastq_id in fastq_ids_list:
        # Get the instrument run id
        instrument_run_id = get_instrument_run_id_from_fastq_id(fastq_id)
        # If the instrument run id is not in the dict, add it
        if instrument_run_id not in instrument_run_id_dict:
            instrument_run_id_dict[instrument_run_id] = []
        instrument_run_id_dict[instrument_run_id].append(fastq_id)

    # Map the dict to a list of objects
    instrument_run_id_list = []
    for instrument_run_id, fastq_ids in instrument_run_id_dict.items():
        instrument_run_id_list.append({
            "instrumentRunId": instrument_run_id,
            "fastqIdList": fastq_ids
        })

    return {
        "fastqIdsByInstrumentRunId": instrument_run_id_list
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "fastqIdList": [
#                         "fqr.01JP12M6BJ041G2VMCKGW4VNNC"
#                     ]
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "fastqIdsByInstrumentRunId": [
#     #         {
#     #             "instrumentRunId": "240424_A01052_0193_BH7JMMDRX5",
#     #             "fastqIdList": [
#     #                 "fqr.01JP12M6BJ041G2VMCKGW4VNNC"
#     #             ]
#     #         }
#     #     ]
#     # }