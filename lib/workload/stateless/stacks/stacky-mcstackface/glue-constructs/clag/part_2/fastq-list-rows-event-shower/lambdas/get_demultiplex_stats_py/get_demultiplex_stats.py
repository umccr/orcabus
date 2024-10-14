#!/usr/bin/env python

"""
Given a demux.csv path and an instrument run id,

Pair the read counts, and quality match scores with a fastq list row id

Given we run fastqc, the only relevant information is the read count

Lane,SampleID,Index,# Reads,# Perfect Index Reads,# One Mismatch Index Reads,# Two Mismatch Index Reads,% Reads,% Perfect Index Reads,% One Mismatch Index Reads,% Two Mismatch Index Reads
1,LPRJ241644,CTGATCGT-GCGCATAT,1115618424,1100614240,15004184,0,0.3422,0.9866,0.0134,0.0000
1,LPRJ241645,ACTCTCGA-CTGTACCA,761004667,751268217,9736450,0,0.2335,0.9872,0.0128,0.0000
1,LPRJ241646,TGAGCTAG-ACCGGTTA,718053113,709117597,8935516,0,0.2203,0.9876,0.0124,0.0000
1,LPRJ241653,ATCGATCG-TGGAAGCA,416153434,404733328,11420106,0,0.1277,0.9726,0.0274,0.0000
1,Undetermined,,248852075,248852075,0,0,0.0763,1.0000,0.0000,0.0000
2,LPRJ241647,GAGACGAT-GAACGGTT,884772616,866133764,18638852,0,0.2638,0.9789,0.0211,0.0000
2,LPRJ241648,CTTGTCGA-CGATGTTC,817203045,808993518,8209527,0,0.2437,0.9900,0.0100,0.0000
2,LPRJ241649,TTCCAAGG-CTACAAGG,803395119,792639954,10755165,0,0.2396,0.9866,0.0134,0.0000
2,LPRJ241654,GCAAGATC-AGTCGAAG,533059421,525802391,7257030,0,0.1589,0.9864,0.0136,0.0000
2,Undetermined,,315283401,315283401,0,0,0.0940,1.0000,0.0000,0.0000
3,LPRJ241650,CGCATGAT-AAGCCTGA,787405495,780175100,7230395,0,0.2385,0.9908,0.0092,0.0000
3,LPRJ241651,ACGGAACA-ACGAGAAC,799004270,791310089,7694181,0,0.2420,0.9904,0.0096,0.0000
3,LPRJ241652,CGGCTAAT-CTCGTTCT,858854271,847914368,10939903,0,0.2601,0.9873,0.0127,0.0000
3,LPRJ241653,ATCGATCG-TGGAAGCA,284364893,276564021,7800872,0,0.0861,0.9726,0.0274,0.0000
3,LPRJ241654,GCAAGATC-AGTCGAAG,256802569,252549724,4252845,0,0.0778,0.9834,0.0166,0.0000
3,Undetermined,,315445082,315445082,0,0,0.0955,1.0000,0.0000,0.0000
4,L2401469,GCGATTAA-GATCTGCT,535609536,529857703,5751833,0,0.1548,0.9893,0.0107,0.0000
4,L2401470,ATTCAGAA-AGGCTATA,564242711,557461667,6781044,0,0.1631,0.9880,0.0120,0.0000
4,L2401471,GAATAATC-GCCTCTAT,540809568,534156451,6653117,0,0.1563,0.9877,0.0123,0.0000
4,L2401472,TTAATCAG-CTTCGCCT,448535365,442654228,5881137,0,0.1297,0.9869,0.0131,0.0000
4,L2401473,CGCTCATT-TAAGATTA,539917611,534300724,5616887,0,0.1561,0.9896,0.0104,0.0000
4,L2401474,TCCGCGAA-AGTAAGTA,546591434,538986434,7605000,0,0.1580,0.9861,0.0139,0.0000
4,L2401475,ATTACTCG-GACTTCCT,1230685,1207314,23371,0,0.0004,0.9810,0.0190,0.0000
4,Undetermined,,282269526,282269526,0,0,0.0816,1.0000,0.0000,0.0000
"""

# Standard imports
from pathlib import Path
import pandas as pd
import boto3
import typing
import logging
import tempfile
from os import environ

# Wrapica
from wrapica.project_data import (
    ProjectData, convert_uri_to_project_data_obj, read_icav2_file_contents
)

# Type checking
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

# Set loggers
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_secret(secret_id: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_id)["SecretString"]


# Functions
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )



def get_demultiplex_stats(demux_csv_project_data_obj: ProjectData, instrument_run_id: str) -> pd.DataFrame:
    """
    Get the demux df
    :param demux_csv_project_data_obj:
    :param instrument_run_id:
    :return:
    """
    with tempfile.NamedTemporaryFile(suffix=".csv") as temp_file:
        read_icav2_file_contents(
            demux_csv_project_data_obj.project_id,
            demux_csv_project_data_obj.data.id,
            output_path=Path(temp_file.name)
        )

        demux_df = pd.read_csv(
            temp_file.name
        ).query("SampleID != 'Undetermined'")

    # Get the fastq list row rgid by combining the index, lane, instrument run id and the sample id
    demux_df['fastqListRowRgid'] = demux_df.apply(
        lambda row: ".".join([
          row['Index'].replace("-", "."),
          str(row['Lane']),
          instrument_run_id,
          row['SampleID'],
        ]),
        axis='columns'
    )

    return demux_df


def demux_stats_df_to_json(demux_stats_df: pd.DataFrame) -> dict:
    """
    Convert the demux stats df to a json
    :param demux_stats_df:
    :return:
    """
    return demux_stats_df.rename(
        columns={
            '# Reads': 'numReads',
        }
    )[[
        "fastqListRowRgid",
        "numReads",
    ]].to_dict(orient='records')


def handler(event, context):
    """
    Given the instrument run id and the path to the Demultiplex Stats csv file,
    Return the read counts and quality match scores paired with the fastq list row id
    :param event:
    :param context:
    :return:
    """
    # Set ICAv2 env vars
    set_icav2_env_vars()

    # Get the project data
    demux_csv_project_data_obj = convert_uri_to_project_data_obj(
        event['demux_uri']
    )

    # Get the demux stats df
    demux_stats_df = get_demultiplex_stats(
        demux_csv_project_data_obj,
        event['instrument_run_id']
    )

    # Convert the demux stats df to a json
    return {
        "read_count_by_fastq_list_row": demux_stats_df_to_json(demux_stats_df)
    }


# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-production"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "demux_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/241004_A01052_0233_AHW5KMDSXC/20241006450c797a/Reports/Demultiplex_Stats.csv",
#                     "instrument_run_id": "241004_A01052_0233_AHW5KMDSXC"
#                 },
#                 None,
#             ),
#             indent=4
#         )
#     )
#
#     # Yields
#     # {
#     #     "read_count_by_fastq_list_row": [
#     #         {
#     #             "fastqListRowRgid": "CTGATCGT.GCGCATAT.1.241004_A01052_0233_AHW5KMDSXC.LPRJ241644",
#     #             "numReads": 1115618424
#     #         },
#     #         {
#     #             "fastqListRowRgid": "ACTCTCGA.CTGTACCA.1.241004_A01052_0233_AHW5KMDSXC.LPRJ241645",
#     #             "numReads": 761004667
#     #         },
#     #         {
#     #             "fastqListRowRgid": "TGAGCTAG.ACCGGTTA.1.241004_A01052_0233_AHW5KMDSXC.LPRJ241646",
#     #             "numReads": 718053113
#     #         },
#     #         {
#     #             "fastqListRowRgid": "ATCGATCG.TGGAAGCA.1.241004_A01052_0233_AHW5KMDSXC.LPRJ241653",
#     #             "numReads": 416153434
#     #         },
#     #         {
#     #             "fastqListRowRgid": "GAGACGAT.GAACGGTT.2.241004_A01052_0233_AHW5KMDSXC.LPRJ241647",
#     #             "numReads": 884772616
#     #         },
#     #         {
#     #             "fastqListRowRgid": "CTTGTCGA.CGATGTTC.2.241004_A01052_0233_AHW5KMDSXC.LPRJ241648",
#     #             "numReads": 817203045
#     #         },
#     #         {
#     #             "fastqListRowRgid": "TTCCAAGG.CTACAAGG.2.241004_A01052_0233_AHW5KMDSXC.LPRJ241649",
#     #             "numReads": 803395119
#     #         },
#     #         {
#     #             "fastqListRowRgid": "GCAAGATC.AGTCGAAG.2.241004_A01052_0233_AHW5KMDSXC.LPRJ241654",
#     #             "numReads": 533059421
#     #         },
#     #         {
#     #             "fastqListRowRgid": "CGCATGAT.AAGCCTGA.3.241004_A01052_0233_AHW5KMDSXC.LPRJ241650",
#     #             "numReads": 787405495
#     #         },
#     #         {
#     #             "fastqListRowRgid": "ACGGAACA.ACGAGAAC.3.241004_A01052_0233_AHW5KMDSXC.LPRJ241651",
#     #             "numReads": 799004270
#     #         },
#     #         {
#     #             "fastqListRowRgid": "CGGCTAAT.CTCGTTCT.3.241004_A01052_0233_AHW5KMDSXC.LPRJ241652",
#     #             "numReads": 858854271
#     #         },
#     #         {
#     #             "fastqListRowRgid": "ATCGATCG.TGGAAGCA.3.241004_A01052_0233_AHW5KMDSXC.LPRJ241653",
#     #             "numReads": 284364893
#     #         },
#     #         {
#     #             "fastqListRowRgid": "GCAAGATC.AGTCGAAG.3.241004_A01052_0233_AHW5KMDSXC.LPRJ241654",
#     #             "numReads": 256802569
#     #         },
#     #         {
#     #             "fastqListRowRgid": "GCGATTAA.GATCTGCT.4.241004_A01052_0233_AHW5KMDSXC.L2401469",
#     #             "numReads": 535609536
#     #         },
#     #         {
#     #             "fastqListRowRgid": "ATTCAGAA.AGGCTATA.4.241004_A01052_0233_AHW5KMDSXC.L2401470",
#     #             "numReads": 564242711
#     #         },
#     #         {
#     #             "fastqListRowRgid": "GAATAATC.GCCTCTAT.4.241004_A01052_0233_AHW5KMDSXC.L2401471",
#     #             "numReads": 540809568
#     #         },
#     #         {
#     #             "fastqListRowRgid": "TTAATCAG.CTTCGCCT.4.241004_A01052_0233_AHW5KMDSXC.L2401472",
#     #             "numReads": 448535365
#     #         },
#     #         {
#     #             "fastqListRowRgid": "CGCTCATT.TAAGATTA.4.241004_A01052_0233_AHW5KMDSXC.L2401473",
#     #             "numReads": 539917611
#     #         },
#     #         {
#     #             "fastqListRowRgid": "TCCGCGAA.AGTAAGTA.4.241004_A01052_0233_AHW5KMDSXC.L2401474",
#     #             "numReads": 546591434
#     #         },
#     #         {
#     #             "fastqListRowRgid": "ATTACTCG.GACTTCCT.4.241004_A01052_0233_AHW5KMDSXC.L2401475",
#     #             "numReads": 1230685
#     #         }
#     #     ]
#     # }
