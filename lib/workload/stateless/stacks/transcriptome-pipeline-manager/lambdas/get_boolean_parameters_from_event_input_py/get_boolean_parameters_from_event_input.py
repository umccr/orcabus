#!/usr/bin/env python3

"""
Get the boolean parameters from the event input
"""
from typing import Dict


def handler(event, context) -> Dict[str, Dict]:
    """
    Get the boolean parameters from the event input
    :param event:
    :param context:
    :return: Dictionary of boolean parameters
    """

    # Collect the event data input
    event_data_input: Dict = event['event_data_input']

    # Get the boolean parameters from the event input
    cwl_parameter_dict: Dict = {
        "enable_duplicate_marking": event_data_input.get('enableDuplicateMarking', False),
        # Add in the cwltools overrides into this step
        "cwltool:overrides": {
            # Biocontainer overrides
            "workflow.cwl#dragen-transcriptome-pipeline--4.2.4/run_qualimap_step": {
                "requirements": {
                    "DockerRequirement": {
                        "dockerPull": "quay.io/biocontainers/qualimap:2.2.2d--hdfd78af_2"
                    }
                }
            },
            "workflow.cwl#dragen-transcriptome-pipeline--4.2.4/arriba_fusion_step": {
                "requirements": {
                    "DockerRequirement": {
                        "dockerPull": "quay.io/biocontainers/arriba:2.4.0--ha04fe3b_0"
                    }
                }
            },
            "workflow.cwl#dragen-transcriptome-pipeline--4.2.4/arriba_drawing_step": {
                "requirements": {
                    "DockerRequirement": {
                        "dockerPull": "quay.io/biocontainers/arriba:2.4.0--ha04fe3b_0"
                    }
                }
            },
            # F2 Image
            "workflow.cwl#dragen-transcriptome-pipeline--4.2.4/run_dragen_transcriptome_step": {
                "requirements": {
                    "DockerRequirement": {
                        "dockerPull": "079623148045.dkr.ecr.us-east-1.amazonaws.com/cp-prod/627166f0-ab0e-40f4-a191-91e6fcaf50d2:latest"
                    },
                    "ResourceRequirement": {
                        "coresMin": 24,
                        "ramMin": 256000,
                        "https://platform.illumina.com/rdf/ica/resources:tier": "standard",
                        "https://platform.illumina.com/rdf/ica/resources:type": "fpga2",
                        "https://platform.illumina.com/rdf/ica/resources:size": "medium",
                    }
                }
            },
        }
    }

    # Remove the None values from the dictionary
    cwl_parameter_dict = dict(
        filter(
            lambda kv: kv[1] is not None,
            cwl_parameter_dict.items()
        )
    )

    # Set map align output booleans
    cwl_parameter_dict['enable_map_align_output'] = True

    # Return the boolean parameters
    return {
        "boolean_parameters": cwl_parameter_dict
    }


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "event_data_input": {}
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "boolean_parameters": {
#     #         "enable_duplicate_marking": false,
#     #         "enable_map_align_output": true
#     #     }
#     # }
