#!/usr/bin/env python3

"""
Given a disease code, get the disease label
"""
# Imports
from gzip import BadGzipFile
from pathlib import Path
import pandas as pd
from tempfile import NamedTemporaryFile
import requests

from ..utils.compression_helpers import decompress_file

# Compressed version of
# https://velserapm.atlassian.net/wiki/download/attachments/86704490/SNOMED_CT%20Disease_trees.xlsx?version=1&modificationDate=1561395438000&api=v2
SNOMED_CT_DISEASE_TREE_FILE = Path(__file__).parent / "snomed_ct_disease_tree.json.gz"
SNOMED_CT_DISEASE_TREE_GITHUB_RAW_URL = "https://github.com/umccr/orcabus/raw/refs/heads/main/lib/workload/stateless/stacks/pieriandx-pipeline-manager/layers/src/pieriandx_pipeline_tools/pieriandx_lookup/snomed_ct_disease_tree.json.gz"


def get_disease_tree() -> pd.DataFrame:
    """
    Returns a dataframe with the following columns
    * Code
    * CodeSystem
    * Label
    :return:
    """
    # Decompress the disease tree file into a temp file
    decompressed_disease_tree_file = NamedTemporaryFile(suffix=".json")

    try:
        decompress_file(SNOMED_CT_DISEASE_TREE_FILE, Path(decompressed_disease_tree_file.name))
    except BadGzipFile:
        # Git LFS not supported on CodePipeline Deployments
        # Write to file
        with NamedTemporaryFile(suffix=".json.gz") as download_h:
            download_h.write(requests.get(SNOMED_CT_DISEASE_TREE_GITHUB_RAW_URL).content)
            download_h.flush()
            decompress_file(Path(download_h.name), Path(decompressed_disease_tree_file.name))

    return pd.read_json(decompressed_disease_tree_file.name)


def get_disease_label_from_disease_code(disease_code: int) -> str:
    """
    Given the disease code, get the disease label
    :param disease_code:
    :return:
    """

    # Get the disease tree
    disease_tree_df = get_disease_tree()

    # Query disease code
    query_df = disease_tree_df.query(
        f"Code=={disease_code}"
    )

    # Assert that the query df is of length 1
    assert query_df.shape[0] == 1, f"Failed to get disease code {disease_code}"

    # Return the label
    return query_df['Label'].item()
