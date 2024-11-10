#!/usr/bin/env python3

"""
Generate a DNA payload for the oncoanalyser event

   "inputs": {
     "mode": "wgts | targeted"
     "analysis_type": "DNA | RNA | DNA/RNA"
     "subject_id": "<subject_id>", // Required
     "tumor_rna_sample_id": "<rna_sample_id>",  // Required if analysis_type is set to RNA
     "tumor_rna_fastq_uri_list": [ <Array of wts fastq list rows> ]  // Required if analysis_type is set to RNA
   },
   "tags": {
      "tumorRnaLibraryId": "<rna_sample_id>", // Present if analysis_type is set to RNA
      "subjectId": "<subject_id>",
      "individualId": "<individual_id>",
   }

{
   "inputs": {
     "mode": "wgts | targeted"
     "analysisType": "DNA | RNA | DNA/RNA"
     "subjectId": "<subject_id>", // Required
     "tumorDnaSampleId": "<tumor_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "normalDnaSampleId": "<normal_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "tumorDnaBamUri": "<tumor_bam_uri>",  // Required if analysis_type is set to DNA
     "normalDnaBamUri": "<normal_bam_uri>",  // Required if analysis_type is set to DNA
   },
   "tags": {
      "tumorDnaLibraryId": "<tumor_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "normalDnaLibraryId": "<normal_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "tumorRnaLibraryId": "<rna_sample_id>", // Present if analysis_type is set to RNA
      "subjectId": "<subject_id>",
      "individualId": "<individual_id>",
   }
}

"""

# GLOBALS
MODE = "wgts"
ANALYSIS_TYPE = "DNA"

# Functions
from typing import Dict, List
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def join_url_paths(url: str, path_ext: str) -> str:
    """
    Join the url paths
    :param url: str
    :param path_ext: str
    :return: url
    """
    url_obj = urlparse(url)
    url_path = Path(url_obj.path) / path_ext

    return str(
        urlunparse(
            (
                url_obj.scheme,
                url_obj.netloc,
                str(url_path),
                None, None, None
            )
        )
    )


def handler(event, context) -> Dict:
    """
    Generate draft event payload for the event
    :param event: event object
    :return: draft event payload
    """
    tumor_library_id = event['tumor_library_id']
    normal_library_id = event['normal_library_id']
    dragen_somatic_output_s3_uri = event['dragen_somatic_output_s3_uri']
    dragen_germline_output_s3_uri = event['dragen_germline_output_s3_uri']

    subject_id = event['subject_id']
    individual_id = event['individual_id']
    tumor_fastq_list_row_ids: List[str] = event['tumor_fastq_list_row_ids']
    normal_fastq_list_row_ids: List[str] = event['normal_fastq_list_row_ids']

    return {
        "input_event_data": {
            "mode": MODE,
            "analysisType": ANALYSIS_TYPE,
            "subjectId": subject_id.replace(" ", "_"),
            "tumorDnaSampleId": tumor_library_id,
            "normalDnaSampleId": normal_library_id,
            "tumorDnaBamUri": join_url_paths(dragen_somatic_output_s3_uri, tumor_library_id + "_tumor.bam"),
            "normalDnaBamUri": join_url_paths(dragen_somatic_output_s3_uri, normal_library_id + "_normal.bam"),
        },
        "event_tags": {
            "subjectId": subject_id,
            "individualId": individual_id,
            "tumorLibraryId": tumor_library_id,
            "normalLibraryId": normal_library_id,
            "tumorFastqListRowIds": tumor_fastq_list_row_ids,
            "normalFastqListRowIds": normal_fastq_list_row_ids,
            "dragenSomaticOutputS3Uri": dragen_somatic_output_s3_uri,
            "dragenGermlineOutputS3Uri": dragen_germline_output_s3_uri,
        }
    }


# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "subject_id": "SN_PMC-141",
#                     "tumor_fastq_list_row_ids": [
#                         "TCGTAGTG.CCAAGTCT.2.240229_A00130_0288_BH5HM2DSXC.L2400231",
#                         "TCGTAGTG.CCAAGTCT.3.240229_A00130_0288_BH5HM2DSXC.L2400231"
#                     ],
#                     "dragen_somatic_output_s3_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/tumor-normal/20241003500edb11/L2400231_dragen_somatic/",
#                     "normal_library_id": "L2400238",
#                     "tumor_library_id": "L2400231",
#                     "normal_fastq_list_row_ids": [
#                         "GGAGCGTC.GCACGGAC.2.240229_A00130_0288_BH5HM2DSXC.L2400238",
#                         "GGAGCGTC.GCACGGAC.3.240229_A00130_0288_BH5HM2DSXC.L2400238"
#                     ],
#                     "dragen_germline_output_s3_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/tumor-normal/20241003500edb11/L2400238_dragen_germline/",
#                     "individual_id": "SBJ04659"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#     # {
#     #     "input_event_data": {
#     #         "mode": "wgts",
#     #         "analysisType": "DNA",
#     #         "subjectId": "SN_PMC-141",
#     #         "tumorDnaSampleId": "L2400231",
#     #         "normalDnaSampleId": "L2400238",
#     #         "tumorDnaBamUri": "pipeline-dev-cache-503977275616-ap-southeast-2://s3/byob-icav2/development/analysis/tumor-normal/20241003500edb11/L2400231_dragen_somatic/L2400231_tumor.bam",
#     #         "normalDnaBamUri": "pipeline-dev-cache-503977275616-ap-southeast-2://s3/byob-icav2/development/analysis/tumor-normal/20241003500edb11/L2400231_dragen_somatic/L2400238_normal.bam"
#     #     },
#     #     "event_tags": {
#     #         "subjectId": "SN_PMC-141",
#     #         "individualId": "SBJ04659",
#     #         "tumorLibraryId": "L2400231",
#     #         "normalLibraryId": "L2400238",
#     #         "tumorFastqListRowIds": [
#     #             "TCGTAGTG.CCAAGTCT.2.240229_A00130_0288_BH5HM2DSXC.L2400231",
#     #             "TCGTAGTG.CCAAGTCT.3.240229_A00130_0288_BH5HM2DSXC.L2400231"
#     #         ],
#     #         "normalFastqListRowIds": [
#     #             "GGAGCGTC.GCACGGAC.2.240229_A00130_0288_BH5HM2DSXC.L2400238",
#     #             "GGAGCGTC.GCACGGAC.3.240229_A00130_0288_BH5HM2DSXC.L2400238"
#     #         ],
#     #         "dragenSomaticOutputS3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/tumor-normal/20241003500edb11/L2400231_dragen_somatic/",
#     #         "dragenGermlineOutputS3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/tumor-normal/20241003500edb11/L2400238_dragen_germline/"
#     #     }
#     # }