#!/usr/bin/env python

"""
Convert b64gzip to dict or vice versa
"""


from typing import Union, Dict, List
from base64 import b64decode
import gzip
import json


def decompress_dict(input_compressed_b64gz_str: str) -> Union[Dict, List]:
    """
    Given a base64 encoded string, decompress and return the original dictionary
    Args:
        input_compressed_b64gz_str:

    Returns: decompressed dictionary or list
    """

    # Decompress
    return json.loads(
        gzip.decompress(
            b64decode(input_compressed_b64gz_str.encode('utf-8'))
        )
    )


def handler(event, context):
    """
    Given a samplesheet compressed, return the library ids
    :param event:
    :param context:
    :return:
    """

    return {
        "libraryIdList": list(map(
            lambda bclconvert_data_row_iter_: bclconvert_data_row_iter_['sample_id'],
            decompress_dict(event['samplesheetB64gz'])['bclconvert_data']
        ))
    }


# if __name__ == "__main__":
#     print(json.dumps(
#         handler(
#             {
#                 "samplesheetB64gz": "H4sIAHS9FmgC/61XUW/aMBD+K1X2OipiDCTsyfODNWnry/wyTdPJJKaLGhIaQjtU9b/vHIhL3JFFilVUgWO+7+78ne/jJfitVaqrYHXzEmyyXMOmrLaqhidd7bOywHXy8SaoDgUUaqvxYyD3jwWZTymJgHxTRzIPcENW7OvqsNVFDfVx1+y7K5/Ud/0YvJrvI8m+4TDvIITkmOTarITz8PwciLuaFan+c7k5sosXeyNDsE7ypCww6Br2uq6z4v5EV+JSlaX6bXvwA8E/fYnMy7w10e/LTf2sKn2RdUBvye0ycLBTVSt8+PMlyFVhsjRh7tV2h4XLUvO1r1iaKV0ugzZUsyikkFwIZhdJs8oFZ0xwQ/JfwKgDKCXniCm7gAjGJONyEGDcAUQ4yRnnToQCw8PQhwBG027KHOGYEE6EUmDOUgwCDDuATGLCgr2rIUM4zgYBzpxD4Vgs5qTMTCXEsEOJnBpi8bFgzqEgWJN0B5D4lg3xLRviWzbEt2yIb9kQ37IhvmUz8x3hNUDqRIhVZO8AJUMiLgYBzrs6xDhQ2PK9sE3ogwAX3VMWRsCuDlkjJSkHATqtx4yA3U4RjZT4sBo6rYfZ4TE7EXIToivsK4Bxt1Oa3LBiTspGM0g0CNDpFGbuBiZcHXJDM6iGMenWUJi7wb2+jNzNddMBpL6FTX0Lm/oWNvUtbOpb2NS3sKlvYVPfwqZehP0L15O8PKRdL3qvC12pWqeXNnN6i3+B/cJzWT1s8vLZPMoSZT9Dk9KFE91lO51nTdDBoSpWWb7Ff4latQ9W6008W8+TzSRZk+WEphs1iehCT1SSLvR6GoUqUR8+Jzk/Iz5RdNUnx3uK5c3sXrUqebauVHW0vw3aZ9BaF7Bu5WL3rtI7eMjqy58Ud6ooT0dx1cZcIYugtTVgncwosriHLIbW8oB1OWPITvbn32TRFFo7BNYBjSILe8hCaK0SWHc0imzWQzaD9i4He32PIqM9ZBTaex7s1T6KbN5DNod2BoC99keRLXrIFtDOB7AjYRRZT1NH2NTn2QF2XIwi62nqCJv6PFfAjpJRZD1NHWFTnz04WNs9hizuaep4Cu2AAzvTRpH1NHUcQjv8wM67UWSkh4xAOxjBzsJBZL9e/wIcbs84hxIAAA==",  # pragma: allowlist secret
#             },
#             None
#         ),
#         indent=4
#     ))