#!/usr/bin/env python3


"""
Take in the event payload,

Given a bclconvertmanager complete event
Convert to a set of inputs for the bssh fastq manager
This will include a
An input URI
An output URI

Use the analysisOutputUri from the bclmanager as the input Uri
Generate the output uri as
icav2://<outputProjectId>/<outputProjectPath>/<instrumentRunId/<__portalRunId__>

Then raise an event saying we have the inputs that we need
"""


def handler(event, context):
    """

    Args:
        event:
        context:

    Returns:

    """
    # TODO