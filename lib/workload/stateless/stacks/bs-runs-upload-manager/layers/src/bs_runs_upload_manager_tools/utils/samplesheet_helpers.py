#!/usr/bin/env python3

"""
Generate samplesheet
"""
from pathlib import Path
import os
import requests
from tempfile import NamedTemporaryFile
import json


def generate_v2_samplesheet(v1_samplesheet_file: Path) -> Path:
    """
    Generate a v2 samplesheet object
    Returns:

    """
    headers = {
        'Authorization': f"Bearer {os.getenv('PORTAL_TOKEN', '')}",
    }

    files = {
        'logLevel': (None, 'ERROR'),
        'file': open(v1_samplesheet_file, 'r'),
    }

    response = requests.post(
        url=os.getenv("PORTAL_API_URL", None),
        headers=headers,
        files=files
    )

    samplesheet_v2_path = Path(NamedTemporaryFile(prefix="SampleSheet", suffix=".csv", delete=False).name)

    with open(samplesheet_v2_path, 'wb') as f:
        f.write(json.loads(response.text).get("v2_samplesheet_str").encode())

    return samplesheet_v2_path
