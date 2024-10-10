#!/usr/bin/env python3

"""
Given a disease code, get the disease label
"""

# Imports
from pathlib import Path
import pandas as pd
from tempfile import NamedTemporaryFile

from ..utils.compression_helpers import decompress_file

# Compressed version of
# https://velserapm.atlassian.net/wiki/download/attachments/86704490/SNOMED_CT%20Disease_trees.xlsx?version=1&modificationDate=1561395438000&api=v2
SNOMED_CT_DISEASE_TREE_FILE = Path(__file__).parent / "snomed_ct_disease_tree.json.gz"


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
    decompress_file(SNOMED_CT_DISEASE_TREE_FILE, Path(decompressed_disease_tree_file.name))

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
