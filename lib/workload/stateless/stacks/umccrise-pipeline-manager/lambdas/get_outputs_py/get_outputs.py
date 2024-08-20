#!/usr/bin/env python3

"""
Get UMCCRise outputs directory
"""

from urllib.parse import (
    urlparse,
    urlunparse
)
from pathlib import Path


def hander(event, context):
    """
    Doesn't really get much simpler than this one,
    take the analysis output uri and the output directory name and simply plonk them together!
    Make sure to add on a trailing slash since we want to note that this output is a directory

    Event input object will look like this
    {
        "analysis_output_uri": "s3://umccr-raw-data/analysis/2019/2019-06-04/2019-06-04_1",
        "output_directory_name": "TUMOR_LIBRARY_ID__NORMAL_LIBRARY_ID"
    }

    :param event:
    :param context:
    :return:
    """

    analysis_output_uri = event["analysis_output_uri"]
    output_directory_name = event["output_directory_name"]

    # Parse the analysis output uri
    parsed_uri = urlparse(analysis_output_uri)

    # Combine the output directory name with the analysis output uri
    output_uri = urlunparse(
        (
            parsed_uri.scheme,
            parsed_uri.netloc,
            # Extend the path with the output directory name
            # Then add in the trailing slash
            str(
                Path(parsed_uri.path) / output_directory_name
            ) + "/",
            None, None, None
        )
    )

    return {
        "output_uri": output_uri
    }

