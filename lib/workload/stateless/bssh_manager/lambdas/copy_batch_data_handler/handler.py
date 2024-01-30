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
    source_uris = list(
        map(
            lambda source_uri_iter: urlparse(source_uri_iter),
            event.get("source_uris")
        )
    )
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

# handler(
# {
#       "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/copy-out-test/folder2/",
#       "source_uris": [
#         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/NovaSeqX-Demo_3664cd_3a7062-BclConvert v4_2_7-0ff58e03-efc1-4e25-bdf5-e3ea835df5dc/bsshoutput.json"
#       ]
#     },
#     None
# )