#!/usr/bin/env python

"""
Read runinfo xml  # FIXME - use new v2-samplesheet-maker to handle runinfo xml parsing / writing
"""

# Standard imports
from typing import Dict
import xmltodict


def parse_runinfo_xml(runinfo_xml_str: str) -> Dict:
    """
    Read runinfo xml
    """
    return xmltodict.parse(runinfo_xml_str)


def get_run_id_from_run_info_xml_dict(run_info_dict: Dict) -> str:
    """
    Get instrument run id from run info xml dict
    """
    return run_info_dict['RunInfo']['Run']['@Id']
