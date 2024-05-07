#!/usr/bin/env python

# Get the path to the sample cache


from pathlib import Path


def generate_sample_cache_path(portal_run_id: str, sample_id: str) -> Path:
    """
    Generate the sample cache path
    Args:
        portal_run_id: str: portal run id
        sample_id: str: sample id

    Returns:
    str: sample cache path
    """
    from .aws_ssm_helpers import get_cttso_root_cache_path

    return Path(get_cttso_root_cache_path()) / portal_run_id / f"{sample_id}_run_cache"


def generate_output_path(portal_run_id: str) -> Path:
    """
    Generate the sample cache path
    Args:
        portal_run_id: str: portal run id
        sample_id: str: sample id

    Returns:
    str: sample cache path
    """
    from .aws_ssm_helpers import get_cttso_root_output_path

    return Path(get_cttso_root_output_path()) / portal_run_id

