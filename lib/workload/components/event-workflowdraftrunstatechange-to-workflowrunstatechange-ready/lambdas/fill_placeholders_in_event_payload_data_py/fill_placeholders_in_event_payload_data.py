#!/usr/bin/env python3

"""
Replace placeholders in the event data payload with actual values

For the special case of portal_run_id, workflow_name and workflow_version, replace the placeholders with the actual values

We can also take the top-level input keys in camel case and convert them to snake case before searching for placeholders to replace them with.

i.e

outputUri: "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/__instrument_run_id__/__portal_run_id__"

can take the instrumentRunId from the event data input dict, and the portal run id from the event input.

We also sanitise values for event data output keys that end in 'Uri' to ensure they are valid URIs

i.e

outputUri: "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_data/__workflow_name__/__workflow_version__/__portal_run_id__"

will take the values cttsov2, 2.1.1 and 20240530abcd1234 and convert this to

outputUri: "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_data/cttsov2/2_1_1/20240530abcd1234" respectively

The output of this function will be a dictionary with the updated event data output values

"""
from copy import deepcopy
from typing import Dict


def sanitise_uri_value(input_value: str) -> str:
    """
    Replace periods to underscores in URIs
    2.1.1 to 2_1_1
    :param input_value:
    :return:
    """
    return input_value.replace('.', '_')


def camel_case_to_snake_case(came_case_input: str) -> str:
    """
    Convert camel case to snake case
    :param came_case_input:
    :return:
    """
    return ''.join(
        [
            '_' + i.lower()
            if i.isupper() else i
            for i in came_case_input
        ]
    ).lstrip('_')


def replace_values_recursively(
        data_dict: Dict,
        portal_run_id: str,
        workflow_name: str,
        workflow_version: str,
        event_data_inputs: Dict
):
    """
    Recursively replace the portal run id placeholder __portal_run_id__ with a portal run id value
    :param data_dict:
    :param portal_run_id:
    :return:
    """

    # We're inside an element of a list of strings
    if isinstance(data_dict, str):
        return data_dict

    # We're inside a dictionary
    data_dict = deepcopy(data_dict)
    for key, value in deepcopy(data_dict).items():
        if isinstance(value, dict):
            data_dict[key] = replace_values_recursively(value, portal_run_id, workflow_name, workflow_version,
                                                        event_data_inputs)
        elif isinstance(value, list):
            data_dict[key] = list(
                map(
                    lambda value_iter: replace_values_recursively(value_iter, portal_run_id, workflow_name,
                                                                  workflow_version, event_data_inputs),
                    deepcopy(data_dict[key])
                )
            )
        elif isinstance(value, str):
            # Replace portal run id
            value = value.replace('__portal_run_id__', portal_run_id)

            # Replace workflow name
            value = value.replace('__workflow_name__', workflow_name)

            # Replace workflow version
            value = value.replace('__workflow_version__', sanitise_uri_value(workflow_version))

            # For each of the event data input keys
            for input_key, input_value in event_data_inputs.items():
                # Only replace if the input value is a string
                if not isinstance(input_value, str):
                    continue

                if key.endswith("Uri"):
                    value = value.replace(f'__{camel_case_to_snake_case(input_key)}__', sanitise_uri_value(input_value))
                else:
                    value = value.replace(f'__{camel_case_to_snake_case(input_key)}__', input_value)

            # Re-assign dict key
            data_dict[key] = value
        else:
            pass

    return data_dict


def handler(event, context):
    # Get the portal run id from the event
    portal_run_id: str = event.get('portal_run_id', None)
    workflow_name: str = event.get('workflow_name', None)
    workflow_version: str = event.get('workflow_version', None)

    # Get the payload data from the event
    event_data_inputs: Dict = event.get('event_data_inputs', None)
    engine_parameters: Dict = event.get('engine_parameters', None)

    # Assert inputs are not None, all are required
    assert portal_run_id is not None, 'Portal run id is required'
    assert workflow_name is not None, 'Workflow name is required'
    assert workflow_version is not None, 'Workflow version is required'
    assert event_data_inputs is not None, 'Input event data is required'
    assert engine_parameters is not None, 'Output event data is required'

    # Recursively replace __portal_run_id__ with the actual portal run id
    engine_parameters_updated = dict(
        replace_values_recursively(
            engine_parameters, portal_run_id, workflow_name,
            workflow_version, event_data_inputs
        )
    )

    # Filter out empty parameters
    engine_parameters_updated = dict(
        filter(
            lambda kv: kv[1] is not None and not kv[1] == "",
            engine_parameters_updated.items()
        )
    )

    return {
        "engine_parameters_updated": engine_parameters_updated
    }

#########################
# PRIMARY ANALYSIS TEST
#########################

# if __name__ == '__main__':
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "portal_run_id": "20240530abcd1234",
#                     "workflow_name": "bsshFastqCopy",
#                     "workflow_version": "4.2.4",
#                     "event_data_inputs": {
#                         "instrumentRunId": "240229_7001234_1234_AHJLJLDS",
#                     },
#                     "engine_parameters": {
#                         "outputUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/__instrument_run_id__/__portal_run_id__/",
#                         "logsUri": "",
#                         "cacheUri": ""
#                     }
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#     # {
#     #   "engine_parameters_updated": {
#     #     "outputUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_7001234_1234_AHJLJLDS/20240530abcd1234/"
#     #   }
#     # }

# #########################
# # SECONDARY ANALYSIS TEST
# #########################
# if __name__ == '__main__':
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "portal_run_id": "20240530abcd1234",
#                     "workflow_name": "cttsov2",
#                     "workflow_version": "2.1.1",
#                     "event_data_inputs": {
#                         "sampleId": "L123456",
#                         "fastqListRows": ["foo", "bar"],
#                     },
#                     "engine_parameters": {
#                         "outputUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_data/__workflow_name__/__workflow_version__/__portal_run_id__/",
#                         "logsUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_logs/__workflow_name__/__workflow_version__/__portal_run_id__/",
#                     }
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # {
#     #   "engine_parameters_updated": {
#     #     "analysisOutputUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_data/cttsov2/2_1_1/20240530abcd1234/",
#     #     "icaLogsUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_logs/cttsov2/2_1_1/20240530abcd1234/"
#     #   }
#     # }
