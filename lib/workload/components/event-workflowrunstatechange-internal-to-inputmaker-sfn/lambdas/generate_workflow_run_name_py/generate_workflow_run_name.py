#!/usr/bin/env python3

"""
Given the name, version and portal run id, return the workflow run name
"""

from typing import Dict


def coerce_names(name: str) -> str:
    """
    Convert a workflow name to lowercase and remove any spacing
    :param name:
    :return:
    """
    name = name.lower().replace(" ", "")
    name = name.replace(".", "-")
    name = name.replace("_", "-")

    return name


def handler(event: Dict, context) -> Dict:
    """
    Generate the workflow run name
    :param event:
    :return:
    """

    # Get the workflow name, version and portal run id from the event
    workflow_name = event.get("workflow_name")
    workflow_version = event.get("workflow_version")
    portal_run_id = event.get("portal_run_id")

    # Assert that the workflow name, version and portal run id are not None
    assert workflow_name is not None
    assert workflow_version is not None
    assert portal_run_id is not None

    # Generate the workflow run name
    return {
        "workflow_run_name": coerce_names(f"umccr__automated__{workflow_name}__{workflow_version}__{portal_run_id}")
    }
