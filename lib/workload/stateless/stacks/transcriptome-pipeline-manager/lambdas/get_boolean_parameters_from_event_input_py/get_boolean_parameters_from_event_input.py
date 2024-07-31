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
        "enable_duplicate_marking": event_data_input.get('enableDuplicateMarking', False)
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
