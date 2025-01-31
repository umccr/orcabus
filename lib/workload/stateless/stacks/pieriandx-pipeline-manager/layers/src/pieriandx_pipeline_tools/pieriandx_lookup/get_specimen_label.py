#!/usr/bin/env python3

"""
Given a specimen code, get the specimen label
"""
from gzip import BadGzipFile

#!/usr/bin/env python3

"""
Given a disease code, get the disease label
"""

# Imports
from pathlib import Path
import pandas as pd
from tempfile import NamedTemporaryFile
from ..utils.compression_helpers import decompress_file
import requests

# Compressed version of
# https://velserapm.atlassian.net/wiki/download/attachments/86704490/SnomedCT-Term_For_SpecimenType.xls?version=1&modificationDate=1561395451000&api=v2
SNOMED_CT_SPECIMEN_TYPE_FILE = Path(__file__).parent / "snomed_ct_specimen_type.json.gz"
SNOMED_CT_SPECIMEN_TYPE_RAW_GITHUB_URL = "https://github.com/umccr/orcabus/raw/refs/heads/main/lib/workload/stateless/stacks/pieriandx-pipeline-manager/layers/src/pieriandx_pipeline_tools/pieriandx_lookup/snomed_ct_specimen_type.json.gz"


def get_specimen_df() -> pd.DataFrame:
    """
    Returns a dataframe with the following columns
    * Code
    * CodeLabel
    * CodeSystem
    :return:
    """
    # Decompress the specimen file into a temp file
    decompressed_specimen_df_file = NamedTemporaryFile(suffix=".json")
    try:
        decompress_file(SNOMED_CT_SPECIMEN_TYPE_FILE, Path(decompressed_specimen_df_file.name))
    except BadGzipFile:
        # Git LFS not supported on CodePipeline Deployments
        # Write to file
        with NamedTemporaryFile(suffix=".json.gz") as download_h:
            download_h.write(requests.get(SNOMED_CT_SPECIMEN_TYPE_RAW_GITHUB_URL).content)
            download_h.flush()
            decompress_file(Path(download_h.name), Path(decompressed_specimen_df_file.name))

    return pd.read_json(decompressed_specimen_df_file.name)


def get_specimen_label_from_specimen_code(specimen_code: int) -> str:
    """
    Given the specimen code, get the specimen label
    :param specimen_code:
    :return:
    """

    # Get the disease tree
    specimen_tree = get_specimen_df()

    # Query disease code
    query_df = specimen_tree.query(
        f"Code=={specimen_code}"
    )

    # Assert that the query df is of length 1
    assert query_df.shape[0] == 1, f"Failed to get specimen code {specimen_code}"

    # Return the label
    return query_df['CodeLabel'].item()
