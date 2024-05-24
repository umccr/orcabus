#!/usr/bin/env python3

"""
Add portal run id to the event payload data recursively,
Replacing __portal_run_id__ with the actual portal run id
"""
from copy import deepcopy
from typing import Dict


def replace_portal_run_id_recursively(data_dict: Dict, portal_run_id: str):
    """
    Recursively replace the portal run id placeholder __portal_run_id__ with a portal run id value
    :param data_dict:
    :param portal_run_id:
    :return:
    """
    data_dict = deepcopy(data_dict)
    for key, value in deepcopy(data_dict).items():
        if isinstance(value, dict):
            data_dict[key] = replace_portal_run_id_recursively(value, portal_run_id)
        elif isinstance(value, list):
            for value_iter in value:
                data_dict[key][value_iter] = replace_portal_run_id_recursively(value_iter, portal_run_id)
        elif isinstance(value, str):
            data_dict[key] = value.replace('__portal_run_id__', portal_run_id)
        else:
            pass

    return data_dict


def handler(event, context):
    # Get the portal run id from the event
    portal_run_id: str = event.get('portal_run_id', None)

    # Get the payload data from the event
    output_event_data: Dict = event.get('output_event_data', None)

    # Assert both portal run id and output event data are not none
    assert portal_run_id is not None, 'Portal run id is required'
    assert output_event_data is not None, 'Output event data is required'

    # Recursively replace __portal_run_id__ with the actual portal run id
    return {
       "event_data_updated":  replace_portal_run_id_recursively(output_event_data, portal_run_id)
    }

