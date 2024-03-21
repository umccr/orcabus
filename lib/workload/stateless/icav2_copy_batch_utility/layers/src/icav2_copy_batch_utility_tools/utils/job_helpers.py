#!/usr/bin/env python3

"""
Submit a copy job
"""

from pathlib import Path
from typing import List
from urllib.parse import urlparse

# Wrapica imports
from wrapica.project_data import convert_icav2_uri_to_data_obj, project_data_copy_batch_handler

# Local imports


def submit_copy_job(dest_uri: str, source_uris: List[str]) -> str:
    # Rerun copy batch process
    source_data_ids = list(
        map(
            lambda source_uri_iter: convert_icav2_uri_to_data_obj(
                source_uri_iter
            ).data.id,
            source_uris
        )
    )

    dest_uri = urlparse(dest_uri)

    return project_data_copy_batch_handler(
        source_data_ids=source_data_ids,
        destination_project_id=dest_uri.netloc,
        destination_folder_path=Path(dest_uri.path)
    ).id
