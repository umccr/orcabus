#!/usr/bin/env python3

"""
Given the results directory of the cttso output directory

Generate the inputs json for the PierianDx manager

cttso-lims-project-name-to-pieriandx-mapping

[
  {
    "project_id": "PO",
    "panel": "subpanel",
    "sample_type": "patient_care_sample",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "COUMN",
    "panel": "subpanel",
    "sample_type": "patient_care_sample",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "CUP",
    "panel": "main",
    "sample_type": "patient_care_sample",
    "is_identified": "identified",
    "default_snomed_disease_code": 285645000
  },
  {
    "project_id": "PPGL",
    "panel": "main",
    "sample_type": "patient_care_sample",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "MESO",
    "panel": "subpanel",
    "sample_type": "patient_care_sample",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "OCEANiC",
    "panel": "subpanel",
    "sample_type": "patient_care_sample",
    "is_identified": "deidentified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "SOLACE2",
    "panel": "main",
    "sample_type": "patient_care_sample",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  },
  {
    "project_id": "IMPARP",
    "panel": "main",
    "sample_type": "patient_care_sample",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  },
  {
    "project_id": "Control",
    "panel": "main",
    "sample_type": "validation",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  },
  {
    "project_id": "QAP",
    "panel": "subpanel",
    "sample_type": "patient_care_sample",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "iPredict2",
    "panel": "subpanel",
    "sample_type": "patient_care_sample",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "*",
    "panel": "main",
    "sample_type": "patient_care_sample",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  }
]


"""

# Standard imports
from os import environ
import boto3
import typing
import json


if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient


def get_ssm_client() -> 'SSMClient':
    return boto3.client('ssm')


def get_ssm_parameter_value(name: str) -> str:
    client = get_ssm_client()
    response = client.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']


def handler(event, context) -> typing.Dict[str, str]:
    pieriandx_configuration_dict = json.loads(get_ssm_parameter_value(environ['PIERIANDX_SAMPLE_CONFIGURATION_SSM_PARAMETER_NAME']))

    # Get the project name / owner
    project_id = event.get('project_id', None)

    return {
        "project_info": next(
            filter(
                lambda project_iter: (
                    (
                        project_iter.get("project_id") == project_id or
                        project_iter.get("project_id") == "*"
                    )
                ),
                pieriandx_configuration_dict
            )
        )
    }

# # PO
# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['PIERIANDX_SAMPLE_CONFIGURATION_SSM_PARAMETER_NAME'] = '/umccr/orcabus/pieriandx/project_info'
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "project_id": "PO"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "project_info": {
#     #         "project_id": "PO",
#     #         "panel": "subpanel",
#     #         "sample_type": "patient_care_sample",
#     #         "is_identified": "identified",
#     #         "default_snomed_term": null
#     #     }
#     # }



# # Default value for projects that do not match in list
# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['PIERIANDX_SAMPLE_CONFIGURATION_SSM_PARAMETER_NAME'] = '/umccr/orcabus/pieriandx/project_info'
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "project_id": "Testing"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "project_info": {
#     #         "project_id": "*",
#     #         "panel": "main",
#     #         "sample_type": "patient_care_sample",
#     #         "is_identified": "deidentified",
#     #         "default_snomed_term": "Neoplastic disease"
#     #     }
#     # }
