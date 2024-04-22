#!/usr/bin/env python

"""
Take a dictionary of source uris where each value is a list of destination uris.

Flip the manifest so that instead the destination uri is the key and the source uris are the value.

In this case, the source uris should be files that reside directory underneath the destination uri.

This allows the copy batch data handler to then easily process each key as a job, since we can have multiple data ids
be copied to the one folder:

Event will look something like either



{
  "manifest": {
    "icav2://project_id/path/to/src/file1": [
      "icav2://project_id/path/to/dest/folder1/",
      "icav2://project_id/path/to/dest/folder2/",
    ],
    "icav2://project_id/path/to/src/file2": [
      "icav2://project_id/path/to/dest/folder2/",
      "icav2://project_id/path/to/dest/folder3/",
    ]
  },
  "manifest_b64gz": "H4sIAAAAAAAAA9XQsU7DMBSF4T1PEXXmYvvaN7a7URhAKhMSICFkXdtJFSlNqqSJVCHenQILEzPs
Z/jO/1aU5apNvOBaiIi6iaQqyI4QjHcEnFMCp1VSWLuUEUXb7XvgnrvTVE8CtVKqCldSScIglcWw
uX3c3tPNw7MNjVJsfNDKN9bAJnXXQ7/U47FcTMBgwaJmYyIBRqzBSGfBRSTwmDJrVmSyF8N8PMxH
sR12k3jisW/73XTZDbvVunw563/4LXmqXYOgMWswyVbAGg2kih1lrp2N9OUPh7Hd83gSKFH//kHo
inxF7nNqJErLMeV5bvM3aHUWvF78r4h3fTP8rYDFe/EBi+cuYYkCAAA=
"
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

Note the output must be decompressed

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
from icav2_copy_batch_utility_tools.utils.compression_helpers import decompress_dict


def handler(event: Dict, context) -> List[Dict]:
    """
    Flip the manifest and return as a list
    :param event:
    :param context:
    :return:
    """

    # Check if we have a manifest
    if event.get("manifest", None) and isinstance(event.get("manifest", None), dict):
        manifest = event.get("manifest")
    elif event.get("manifest_b64gz", None) and isinstance(event.get("manifest_b64gz", None), str):
        manifest = decompress_dict(event.get("manifest_b64gz"))
    else:
        raise ValueError("No manifest found in event")

    # Collect all values from all keys
    all_destination_uris = list(
        set(
            reduce(
                lambda list_1, list_2: list_1 + list_2,
                map(
                    lambda dest_uri_iter: dest_uri_iter,
                    manifest.values()
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
                lambda source_uri_iter_filter: dest_uri in manifest[source_uri_iter_filter],
                manifest.keys()
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


# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "manifest": {
#                         "icav2://project_id/path/to/src/file1": [
#                             "icav2://project_id/path/to/dest/folder1/",
#                             "icav2://project_id/path/to/dest/folder2/",
#                         ],
#                         "icav2://project_id/path/to/src/file2": [
#                             "icav2://project_id/path/to/dest/folder2/",
#                             "icav2://project_id/path/to/dest/folder3/",
#                         ]
#                     }
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     manifest_b64gz = """
# H4sIAAAAAAAAA9XQsU7DMBSF4T1PEXXmYvvaN7a7URhAKhMSICFkXdtJFSlNqqSJVCHenQILEzPs
# Z/jO/1aU5apNvOBaiIi6iaQqyI4QjHcEnFMCp1VSWLuUEUXb7XvgnrvTVE8CtVKqCldSScIglcWw
# uX3c3tPNw7MNjVJsfNDKN9bAJnXXQ7/U47FcTMBgwaJmYyIBRqzBSGfBRSTwmDJrVmSyF8N8PMxH
# sR12k3jisW/73XTZDbvVunw563/4LXmqXYOgMWswyVbAGg2kih1lrp2N9OUPh7Hd83gSKFH//kHo
# inxF7nNqJErLMeV5bvM3aHUWvF78r4h3fTP8rYDFe/EBi+cuYYkCAAA=
#     """.replace("\n", "")
#
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "manifest_b64gz": manifest_b64gz
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     # [
#     #     {
#     #         "dest_uri": "icav2://project_id/path/to/dest/folder1/",
#     #         "source_uris": [
#     #             "icav2://project_id/path/to/src/file1"
#     #         ]
#     #     },
#     #     {
#     #         "dest_uri": "icav2://project_id/path/to/dest/folder2/",
#     #         "source_uris": [
#     #             "icav2://project_id/path/to/src/file1",
#     #             "icav2://project_id/path/to/src/file2"
#     #         ]
#     #     },
#     #     {
#     #         "dest_uri": "icav2://project_id/path/to/dest/folder3/",
#     #         "source_uris": [
#     #             "icav2://project_id/path/to/src/file2"
#     #         ]
#     #     }
#     # ]
#
#     # [
#     #     {
#     #         "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3659658/20240207abcduuid/Logs/",
#     #         "source_uris": [
#     #             "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_f11a49_319f74-BclConvert v4_2_7-723a44b5-2b2e-4087-8b25-92cda3a154d9/output/Logs/Warnings.log",
#     #             "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_f11a49_319f74-BclConvert v4_2_7-723a44b5-2b2e-4087-8b25-92cda3a154d9/output/Logs/Info.log"
#     #         ]
#     #     }
#     # ]

