#!/usr/bin/env python3

"""
Get the data payload python

The outputs (if report status is complete) will comprise the following

# Case url where pieriandx_base_url is one of https://app.pieriandx.com
{pieriandx_base_url}/cgw/order/viewOrderDetails/{case_id}
# VCF Output URL
{pieriandx_base_url}/cgw/informatics/downloadJobOutputAnalysisFile?caseId={case_id}&jobId={job_id}&accessionNumber={case_accession_number}&fileName=main.vcf
# Biomarker Report PDF URL
{pieriandx_base_url}/cgw/informatics/downloadJobOutputAnalysisFile?caseId={case_id}&jobId={job_id}&accessionNumber={case_accession_number}&fileName={sample_name}_BiomarkerReport.txt
# Report PDF URL
{pieriandx_base_url}/cgw/report/openPdfReport/{report_id}

"""

from urllib.parse import (
    urlparse, urlunparse
)
from pathlib import Path


def strip_path_from_url(url: str) -> str:
    """
    Strip the path from the url
    :param url:
    :return:
    """
    url_obj = urlparse(url)

    return str(
        urlunparse(
            (
                url_obj.scheme,
                url_obj.netloc,
                "/",
                None, None, None
            )
        )
    )


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


def handler(event, context):
    """
    Get the data payload with or without the outputs
    :param event:
    :param context:
    :return:
    """

    # Get inputs
    inputs = event.get("inputs")
    engine_parameters = event.get("engine_parameters")
    tags = event.get("tags")
    report_status = event.get("report_status")
    case_id = event.get("case_id")
    job_id = event.get("job_id")
    case_accession_number = event.get("case_accession_number")
    report_id = event.get("report_id")
    pieriandx_base_url = event.get("pieriandx_base_url")
    sample_name = event.get("sample_name")

    # Initial dict
    return_dict = {
        "data_payload": {
            "inputs": inputs,
            "engineParameters": engine_parameters,
            "tags": tags
        }
    }

    # Return if the report generation is not complete yet
    if not report_status in ["report_generation_complete", "complete"]:
        # Return as id
        return return_dict

    # Set the outputs
    return_dict["data_payload"]["outputs"] = {
        "caseUrl": join_url_paths(
            strip_path_from_url(pieriandx_base_url),
            f"/cgw/order/viewOrderDetails/{case_id}"
        ),
        "vcfOutputUrl": join_url_paths(
            strip_path_from_url(pieriandx_base_url),
     f"/cgw/informatics/downloadJobOutputAnalysisFile?caseId={case_id}&jobId={job_id}&accessionNumber={case_accession_number}&fileName=main.vcf"
        ),
        "reportPdfUrl": join_url_paths(
            strip_path_from_url(pieriandx_base_url),
     f"/cgw/report/openPdfReport/{report_id}"
        ),
        "biomarkerReportUrl": join_url_paths(
            strip_path_from_url(pieriandx_base_url),
     f"/cgw/informatics/downloadJobOutputAnalysisFile?caseId={case_id}&jobId={job_id}&accessionNumber={case_accession_number}&fileName={sample_name}_BiomarkerReport.txt"
        ),
    }

    return return_dict


# DEV
# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "inputs": {
#                         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#                         "panelVersion": "main",
#                         "caseMetadata": {
#                             "isIdentified": False,
#                             "caseAccessionNumber": "L2400160__V2__2024100405a12a95",
#                             "externalSpecimenId": "SSq-CompMM-1pc-10646259ilm",
#                             "sampleType": "patientcare",
#                             "specimenLabel": "primarySpecimen",
#                             "indication": "NA",
#                             "diseaseCode": 55342001,
#                             "specimenCode": "122561005",
#                             "sampleReception": {
#                                 "dateAccessioned": "2024-10-04T10:03:11+1000",
#                                 "dateCollected": "2024-10-04T10:03:11+1000",
#                                 "dateReceived": "2024-10-04T10:03:11+1000"
#                             },
#                             "study": {
#                                 "id": "Testing",
#                                 "subjectIdentifier": "CMM1pc-10646259ilm"
#                             }
#                         },
#                         "dataFiles": {
#                             "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/DragenCaller/L2400160/L2400160.microsat_output.json",
#                             "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/Tmb/L2400160/L2400160.tmb.metrics.csv",
#                             "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.cnv.vcf.gz",
#                             "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.hard-filtered.vcf.gz",
#                             "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_Fusions.csv",
#                             "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_MetricsOutput.tsv",
#                             "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#                         }
#                     },
#                     "engine_parameters": {
#                         "caseId": "103779",
#                         "informaticsJobId": "46014"
#                     },
#                     "tags": {
#                         "metadataFromRedCap": False,
#                         "isIdentified": False,
#                         "libraryId": "L2400160",
#                         "sampleType": "patientcare",
#                         "projectId": "Testing",
#                         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#                     },
#                     "report_status": "complete",
#                     "case_id": "103779",
#                     "job_id": "46014",
#                     "case_accession_number": "L2400160__V2__2024100405a12a95",
#                     "report_id": "38152",
#                     "pieriandx_base_url": "https://app.uat.pieriandx.com/cgw-api/v2.0.0",
#                     "sample_name": "L2400160"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "data_payload": {
#     #         "inputs": {
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
#     #             "panelVersion": "main",
#     #             "caseMetadata": {
#     #                 "isIdentified": false,
#     #                 "caseAccessionNumber": "L2400160__V2__2024100405a12a95",
#     #                 "externalSpecimenId": "SSq-CompMM-1pc-10646259ilm",
#     #                 "sampleType": "patientcare",
#     #                 "specimenLabel": "primarySpecimen",
#     #                 "indication": "NA",
#     #                 "diseaseCode": 55342001,
#     #                 "specimenCode": "122561005",
#     #                 "sampleReception": {
#     #                     "dateAccessioned": "2024-10-04T10:03:11+1000",
#     #                     "dateCollected": "2024-10-04T10:03:11+1000",
#     #                     "dateReceived": "2024-10-04T10:03:11+1000"
#     #                 },
#     #                 "study": {
#     #                     "id": "Testing",
#     #                     "subjectIdentifier": "CMM1pc-10646259ilm"
#     #                 }
#     #             },
#     #             "dataFiles": {
#     #                 "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/DragenCaller/L2400160/L2400160.microsat_output.json",
#     #                 "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/Tmb/L2400160/L2400160.tmb.metrics.csv",
#     #                 "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.cnv.vcf.gz",
#     #                 "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.hard-filtered.vcf.gz",
#     #                 "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_Fusions.csv",
#     #                 "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_MetricsOutput.tsv",
#     #                 "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#     #             }
#     #         },
#     #         "engineParameters": {
#     #             "caseId": "103779",
#     #             "informaticsJobId": "46014"
#     #         },
#     #         "tags": {
#     #             "metadataFromRedCap": false,
#     #             "isIdentified": false,
#     #             "libraryId": "L2400160",
#     #             "sampleType": "patientcare",
#     #             "projectId": "Testing",
#     #             "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#     #         },
#     #         "outputs": {
#     #             "caseUrl": "https://app.uat.pieriandx.com/cgw-api/v2.0.0/cgw/order/viewOrderDetails/103779",
#     #             "vcfOutputUrl": "https://app.uat.pieriandx.com/cgw-api/v2.0.0/cgw/informatics/downloadJobOutputAnalysisFile?caseId=103779&jobId=46014&accessionNumber=L2400160__V2__2024100405a12a95&fileName=main.vcf",
#     #             "reportPdfUrl": "https://app.uat.pieriandx.com/cgw-api/v2.0.0/cgw/report/openPdfReport/38152",
#     #             "biomarkerReportUrl": "https://app.uat.pieriandx.com/cgw-api/v2.0.0/cgw/informatics/downloadJobOutputAnalysisFile?caseId=103779&jobId=46014&accessionNumber=L2400160__V2__2024100405a12a95&fileName=L2400160_BiomarkerReport.txt"
#     #         }
#     #     }
#     # }


# # PROD
# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "pieriandx_base_url": "https://app.pieriandx.com/cgw-api/v2.0.0",
#                     "inputs": {
#                         "instrumentRunId": "241101_A01052_0236_BHVJNMDMXY",
#                         "panelVersion": "main",
#                         "caseMetadata": {
#                             "isIdentified": False,
#                             "caseAccessionNumber": "L2401562__V2__20241106c25602c7",
#                             "externalSpecimenId": "CMM0.5pc-10646979",
#                             "sampleType": "validation",
#                             "specimenLabel": "primarySpecimen",
#                             "indication": "NA",
#                             "diseaseCode": 55342001,
#                             "specimenCode": "122561005",
#                             "sampleReception": {
#                                 "dateAccessioned": "2024-11-07T08:39:55+1100",
#                                 "dateCollected": "2024-11-07T08:39:55+1100",
#                                 "dateReceived": "2024-11-07T08:39:55+1100"
#                             },
#                             "study": {
#                                 "id": "Control",
#                                 "subjectIdentifier": "Sera-ctDNA-Comp05pc"
#                             }
#                         },
#                         "dataFiles": {
#                             "microsatOutputUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Logs_Intermediates/DragenCaller/L2401562/L2401562.microsat_output.json",
#                             "tmbMetricsUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Logs_Intermediates/Tmb/L2401562/L2401562.tmb.metrics.csv",
#                             "cnvVcfUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562.cnv.vcf.gz",
#                             "hardFilteredVcfUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562.hard-filtered.vcf.gz",
#                             "fusionsUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562_Fusions.csv",
#                             "metricsOutputUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562_MetricsOutput.tsv",
#                             "samplesheetUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#                         }
#                     },
#                     "job_id": "302091",
#                     "report_id": "312010",
#                     "case_id": "336486",
#                     "report_status": "complete",
#                     "case_accession_number": "L2401562__V2__20241106c25602c7",
#                     "engine_parameters": {
#                         "caseId": "336486",
#                         "informaticsJobId": "302091"
#                     },
#                     "tags": {
#                         "metadataFromRedCap": False,
#                         "isIdentified": False,
#                         "libraryId": "L2401562",
#                         "sampleType": "validation",
#                         "projectId": "Control",
#                         "instrumentRunId": "241101_A01052_0236_BHVJNMDMXY",
#                         "panelVersion": "main"
#                     },
#                     "sample_name": "L2401562"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "data_payload": {
#     #         "inputs": {
#     #             "instrumentRunId": "241101_A01052_0236_BHVJNMDMXY",
#     #             "panelVersion": "main",
#     #             "caseMetadata": {
#     #                 "isIdentified": false,
#     #                 "caseAccessionNumber": "L2401562__V2__20241106c25602c7",
#     #                 "externalSpecimenId": "CMM0.5pc-10646979",
#     #                 "sampleType": "validation",
#     #                 "specimenLabel": "primarySpecimen",
#     #                 "indication": "NA",
#     #                 "diseaseCode": 55342001,
#     #                 "specimenCode": "122561005",
#     #                 "sampleReception": {
#     #                     "dateAccessioned": "2024-11-07T08:39:55+1100",
#     #                     "dateCollected": "2024-11-07T08:39:55+1100",
#     #                     "dateReceived": "2024-11-07T08:39:55+1100"
#     #                 },
#     #                 "study": {
#     #                     "id": "Control",
#     #                     "subjectIdentifier": "Sera-ctDNA-Comp05pc"
#     #                 }
#     #             },
#     #             "dataFiles": {
#     #                 "microsatOutputUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Logs_Intermediates/DragenCaller/L2401562/L2401562.microsat_output.json",
#     #                 "tmbMetricsUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Logs_Intermediates/Tmb/L2401562/L2401562.tmb.metrics.csv",
#     #                 "cnvVcfUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562.cnv.vcf.gz",
#     #                 "hardFilteredVcfUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562.hard-filtered.vcf.gz",
#     #                 "fusionsUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562_Fusions.csv",
#     #                 "metricsOutputUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Results/L2401562/L2401562_MetricsOutput.tsv",
#     #                 "samplesheetUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411052080dbdd/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#     #             }
#     #         },
#     #         "engineParameters": {
#     #             "caseId": "336486",
#     #             "informaticsJobId": "302091"
#     #         },
#     #         "tags": {
#     #             "metadataFromRedCap": false,
#     #             "isIdentified": false,
#     #             "libraryId": "L2401562",
#     #             "sampleType": "validation",
#     #             "projectId": "Control",
#     #             "instrumentRunId": "241101_A01052_0236_BHVJNMDMXY",
#     #             "panelVersion": "main"
#     #         },
#     #         "outputs": {
#     #             "caseUrl": "https://app.pieriandx.com/cgw/order/viewOrderDetails/336486",
#     #             "vcfOutputUrl": "https://app.pieriandx.com/cgw/informatics/downloadJobOutputAnalysisFile?caseId=336486&jobId=302091&accessionNumber=L2401562__V2__20241106c25602c7&fileName=main.vcf",
#     #             "reportPdfUrl": "https://app.pieriandx.com/cgw/report/openPdfReport/312010",
#     #             "biomarkerReportUrl": "https://app.pieriandx.com/cgw/informatics/downloadJobOutputAnalysisFile?caseId=336486&jobId=302091&accessionNumber=L2401562__V2__20241106c25602c7&fileName=L2401562_BiomarkerReport.txt"
#     #         }
#     #     }
#     # }