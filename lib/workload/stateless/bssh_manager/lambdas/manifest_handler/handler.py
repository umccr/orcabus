#!/usr/bin/env python

"""
Take a dictionary of source uris where each value is a list of destination uris.

Flip the manifest so that instead the destination uri is the key and the source uris are the value.

In this case, the source uris should be files that reside directory underneath the destination uri.

This allows the copy batch data handler to then easily process each key as a job, since we can have multiple data ids
be copied to the one folder:

Event will look something like this:

{
  "icav2://project_id/path/to/src/file1": [
    "icav2://project_id/path/to/dest/folder1/",
    "icav2://project_id/path/to/dest/folder2/",
  ],
  "icav2://project_id/path/to/src/file2": [
    "icav2://project_id/path/to/dest/folder2/",
    "icav2://project_id/path/to/dest/folder3/",
  ],
}

So we flip this to be

{
  "icav2://project_id/path/to/dest/folder1/": [
    "icav2://project_id/path/to/src/file1",
  ],
  "icav2://project_id/path/to/dest/folder2/": [
    "icav2://project_id/path/to/src/file1",
    "icav2://project_id/path/to/src/file2",
  ],
  "icav2://project_id/path/to/dest/folder3/": [
    "icav2://project_id/path/to/src/file2",
  ]
}

Convert to an array as this will help AWS Step Functions deploy the manifest for the copy batch data handler.

We don't convert the uris to data ids incase there are too many, and we worry about lambda time outs,
that can be done by the lambda that generates the copy job

[
  {
    "dest_uri": "icav2://project_id/path/to/dest/folder1/",
    "source_uris": [
        "icav2://project_id/path/to/src/file1",
    ],
  },
  {
    "dest_uri": "icav2://project_id/path/to/dest/folder2/",
    "source_uris": [
        "icav2://project_id/path/to/src/file1",
        "icav2://project_id/path/to/src/file2",
    ],
  },
  {
    "dest_uri": "icav2://project_id/path/to/dest/folder3/",
    "source_uris": [
        "icav2://project_id/path/to/src/file2",
    ]
  }
]

"""
from functools import reduce
from typing import Dict, List


def handler(event: Dict, context) -> List[Dict]:
    """
    Flip the manifest and return as a list
    :param event:
    :param context:
    :return:
    """

    # Collect all values from all keys
    all_destination_uris = list(
        set(
            reduce(
                lambda list_1, list_2: list_1 + list_2,
                map(
                    lambda dest_uri_iter: dest_uri_iter,
                    event.values()
                ),
                []
            )
        )
    )

    # Now invert our manifest by generating a per-destination uri list of source uris
    source_uris_by_dest = {}
    for dest_uri in all_destination_uris:
        source_uris_by_dest[dest_uri] = list(
            filter(
                lambda source_uri_iter_filter: dest_uri in event[source_uri_iter_filter],
                event.keys()
            )
        )

    # Convert the dict to a list where the key is "dest_uri" and "source_uris" represents the value
    return (
        sorted(
            list(
                map(
                    lambda dest_uri_iter_kv: {
                        "dest_uri": dest_uri_iter_kv[0],
                        "source_uris": dest_uri_iter_kv[1]
                    },
                    source_uris_by_dest.items()
                )
            ),
            key=lambda x: x.get("dest_uri")
        )
    )
