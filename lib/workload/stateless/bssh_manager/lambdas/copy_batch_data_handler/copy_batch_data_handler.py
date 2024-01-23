#!/usr/bin/env python3

"""
Given a dest URI and list of source data ids, copy each of the data ids from the source URI to the destination URIs
Returns a list of job IDs

{
  "dest_uri": "icav2://src_project_id/path/to/dest/",
  "source_uris": [
      "icav2://project_id/path/to/src/file1",
      "icav2://project_id/path/to/src/file2",
  ]
}
"""

# Import pathlib from path
from pathlib import Path

# Imports
from urllib.parse import urlparse

# Imports
from bssh_manager_tools.utils.icav2_configuration_handler import set_icav2_env_vars
from bssh_manager_tools.utils.icav2_project_data_handler import (
    get_file_id_from_path,
    project_data_copy_batch_handler
)


def handler(event, context):
    """
    Read in the event and collect the workflow session details
    """
    # Set ICAv2 configuration from secrets
    set_icav2_env_vars()

    # Get the source URI and destination URIs from the event
    source_uris = urlparse(event.get("source_uris"))
    dest_uri = urlparse(event.get("dest_uri"))

    source_data_ids = list(
        map(
            lambda source_uri_iter: get_file_id_from_path(
                source_uri_iter.netloc,
                Path(source_uri_iter.path)
            ),
            source_uris
        )
    )

    return project_data_copy_batch_handler(
        source_data_ids=source_data_ids,
        destination_project_id=dest_uri.netloc,
        destination_folder_path=Path(dest_uri.path).parent
    ).id
