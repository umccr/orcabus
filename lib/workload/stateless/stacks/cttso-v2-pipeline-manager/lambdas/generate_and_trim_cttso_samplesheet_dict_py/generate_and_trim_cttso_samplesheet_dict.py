#!/usr/bin/env python3

"""
Generate cttso samplesheet csv

Takes a b64gzip input or regular json input

{
    "samplesheet_b64gz": "H4sIAAAAAAAA/8tJLS5RsjI2VrJSSdZI",
    "sample_id": "L12345678"
}

Returns the samplesheet b64gz very trimmed and compressed

{
    "samplesheet_b64gz": "H4sIAAAAAAAA/8tJLS5RsjI2VrJSSdZI"
}

"""
from copy import deepcopy
from typing import List, Dict

# Local imports
from cttso_v2_pipeline_manager_tools.utils.compression_helpers import (
    decompress_dict, compress_dict
)

# Globals
READS_SECTION = {
    "read_1_cycles": "151",
    "read_2_cycles": "151",
    "index_1_cycles": "10",
    "index_2_cycles": "10"
}

TSO500L_SETTINGS = {
    "adapter_read_1": "CTGTCTCTTATACACATCT",
    "adapter_read_2": "CTGTCTCTTATACACATCT",
    "adapter_behaviour": "trim",
    "minimum_trimmed_read_length": 35,
    "mask_short_reads": 35,
    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143"
}


def handler(event, context):
    """
    Import
    Args:
        event:
        context:

    Returns:

    """

    # Part 0 - get inputs
    samplesheet_b64gz = event.get("samplesheet_b64gz", None)
    sample_id = event.get("sample_id", None)

    # Check samplesheet_b64gz is an input
    if samplesheet_b64gz is None:
        raise ValueError("No samplesheet_b64gz provided")

    # Check sample id
    if sample_id is None:
        raise ValueError("No sample_id provided")

    # Part 1 - decompress the samplesheet
    samplesheet_dict = decompress_dict(samplesheet_b64gz)

    # Part 2 - edit the samplesheet
    # We only take the 'header', the reads we will set ourselves, TSO500L_Settings ourselves
    # We only take the rows of the TSO500L_Data section where the column Sample_ID matches sample_id
    header = samplesheet_dict.get("header")
    tso500l_sample_id_rows: List[Dict] = list(
        filter(
            lambda tso500_data_row_iter: tso500_data_row_iter.get("sample_id") == sample_id,
            samplesheet_dict.get("tso500l_data")
        )
    )

    # Check we have a row for this sample_id
    if len(tso500l_sample_id_rows) == 0:
        raise ValueError(f"No rows found for sample_id {sample_id}")

    # Update i7 and i5 index id for tso500l data section
    for index, tso500l_sample_id_row in enumerate(deepcopy(tso500l_sample_id_rows)):
        # Check i7 index id
        if tso500l_sample_id_row.get("i7_index_id", None) is None:
            if tso500l_sample_id_row.get("index_id", None) is None:
                ValueError("Please specify either index_id or i7_index_id for all tso500l_data rows")
            tso500l_sample_id_rows[index]["i7_index_id"] = tso500l_sample_id_row["index_id"]
        # Check i5 index id
        if tso500l_sample_id_row.get("i5_index_id", None) is None:
            if tso500l_sample_id_row.get("index_id", None) is None:
                ValueError("Please specify either index_id or i5_index_id for all tso500l_data rows")
            tso500l_sample_id_rows[index]["i5_index_id"] = tso500l_sample_id_row["index_id"]

    # Part 3 - write the samplesheet
    samplesheet_dict: Dict = {
        "header": header,
        "reads": READS_SECTION,
        "tso500l_settings": TSO500L_SETTINGS,
        "tso500l_data": tso500l_sample_id_rows
    }

    # Compress and return
    return {
        "samplesheet_b64gz": compress_dict(samplesheet_dict)
    }


# if __name__ == "__main__":
#     import json
#     samplesheet_b64_gz = """
# H4sIAAAAAAAAA9VaTW/bOBC978/QXpOFPi3JPWlVQCjQzS4a9lAsgoFsK41QW3ZtJ92iyH9fDiVG
# pMKxVMI9GEGTmpL5Zvjx5pEzP5yHqlxVe2f+w7mv1xXcb/eb8ghP1f5Qbxtn7l85+8cGmnJTOXOH
# Hb421zfV4sNN5gee5wXXf72vqlv2AbzZzfbJD5wrp24Ox/3jpmqOcPy+w2/xJ+Vt9dV55n1xtAOC
# 4X/Ag+X35briDV7ktQ/B19vqZlX9p77oyjblRZf3vFiul9uG232EQ3U81s1ngbOpm3rzuIHjvt5s
# qhUIjHXVfD4+OPMgunp5oVyVu2O1hy3vYl3u+EP+rDx8gcPDlvfZGR5EOtSqPJbO/N8fzrpsuKvc
# 4EO52fFxrFfc8fd+4HrBLHE6m3lTkeWsyAqWFbLR5605b81YnmU5b0UL9vWqevHP+RjfeJ+8MHjz
# znPFP9nA35Z2twPKX84K3lNRZPxvwfvN8oIhJEfIcw6cZ8Mv+cMv8ZcKhiZiA7bwD3zyTjuZKk4K
# GO5pkalOMuyXm8I7u1AnY1dxMuffz/iXWK46meWiJ/7gYp30tOWKONiB5iTvORcWXayTvjqTjKE7
# jGnLNefN2HF2ucs10GYSeynaOVNmkonu80tYrr7JyXDGO+MhSqOfln/0+USCZaxj3st0NX7lqgDG
# DcoG+5OJiJJdrKvJ61lliMiyQeTkFnE7ivxyXU1fuSpCZzEkJN4rus8uIn4aXY3c17PKwVEWFMMo
# ih0WFxFgjK7GoeKkWLisY9mekLBXfHC5TkYaFXEtlGGI0fYnshAac7GLNom0nVmgStf2Jc4h8q3R
# wU/8FPPmXXLjt7/w4yhgrO0P5AFdSOPOQG1iARgYAWfqNOKgZPpKFUNXENHEBlA7ETH8YUwHRAY4
# I6B6OmFCBxUaIJ8+pNyzDWmqnRQEbevCK8fNwt08G6Cu2pk4Tw40gVAKZwNUFTQKDjzb6XPIcHva
# bAszYKCTDe77V3yKi/dsgOrGF/Q9OLWzNkjZDGloAvTVOcxzsee0IUUDumE+D6CveYjLNM8HQ5p1
# C+k8gNqJBO9CmH6ybCnditrMgGoYxunikWJwKmj189kA1UWTIdxglXJqRcl6vjlUybsQJ5xBeOpv
# Kc4DqIYn1GnDbYErlFSpNoBqtEBRyIYXS0JBWgVgM+DgLgsPkwOmwRG1ihZGwECNFgWujkJfpbhG
# u5V7HkCVafAEidtgGIDzM+7DQL9vwWgxDE8FIw+sNoAq07ThV1+lqHK6c/N5AFWmaQWGvkozcUy1
# iodmQJ1pChGNtEWTibuds3kY6lzKua0YeIhcR92vWAD+StVmBPyVIsoMGOqrtBiSN27MIiMuN4yA
# d1fOcr19XGlZkM9VU+3LY7XqEzuO+wf/ceTb37b7L/fr7Tf+oF6WLx8BR0TJd+zqXbWu0R/ncd/M
# 6/WG/1qWc9k+X9ynwSJa3l8vF358Ha7uy+sknFXX5XI1qxZu4pXL8vc/l+u86/ApBB9iTA21drwk
# VAh5tK4X+3L/XSak5BOQcgkUjSTf3e2rHXypj0oW65Z9EHNDaCIzig9SI4EijOxQAhIlACmMQFFD
# dighiRKCVEOgSCA7lIhEiUBKIFB0jx3KjESZgdQ9oIgdO5SYRIlBih1QFI4dSkKiJCAVDiiyxg4l
# JVFSkLIGFC1jhSK0ixElcEFqGVAEjB0KufcDD6SAAUW12KGQez/wQaoWUKSKHQq594MApFQBRZ/Y
# oZB7PwhB6hNQRIkdCrn3A9z7rSgBRYlYoYSkLyHyWKtEQJEfdih9JsmM1T2HPr8EWlKJQl0e2e3f
# Tz4FG4/Ads+hz/WAluCxhE1GYBPp7UveBbRkiyVsOgLbPYc+BwJa4sMOVsk8GGHlc+jzEaAlIexg
# ZyTRzxLoS0FAq/+whCLZfibYvivIAK0Kww4qJik/dqEviwCtFsISiuT92IO+OAG0igRLKJL8YyR/
# WSIAWl2AJRQZAeIA+kQ9aNl5SyiSOuMQ+rwUaMkoSygyFsQR9Nkh0FJCdlAJCZVEIHM0oCRmKJi2
# lo1CISVnMgOZJwElOWKHQkrOJAaZ/gEl52OHQjJRkoBMwYCSd7FDIUkoSUGe4EE5tp8I1DdlsyVg
# UpKAUhdktgWUFIslDEk+KZJPez0Ayp2AJQxJPKkPMrMCSjrFEoYknTQAmU8BJYliCUMSThqCvOIA
# 5V7DEoZkgDQCmawBJUMzCnN35RwP28h119rVyassNIpMPAswIdQFxTiGvPPp1xbVQ/lUbx/3/E0s
# TXWuJlSqGqpRfy6n/ty7eOKeRdHB3cOujvftjZgvmbn+iXKrOoa2aFfAfHz7j+u64kY4MrWP6uRJ
# Zk0ojTKZFRBmBeM6etpojZcxmcwKCbPCcZ09yawJJUcmsyLCrGhch08brfHyIJNZM8Ks2SmdThvk
# aeM0Vr9tMiglDEpPqflJBk2otTYY5Llmg3j7Cc0/yaAJddEmgzzCIO/UyWDilI3WMJsMIvjJO3l+
# mDZC4/XGJoMIZvIoZhKnjIkjNFobbDKI4CSP4iRxFpm07ScUzJkMItjIo9hInFgmBpPR4jaTQQQP
# 8fbnu+ff/gcSZgO3fTMAAA==
#     """.replace("\n", "")
#
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "samplesheet_b64gz": samplesheet_b64_gz,
#                     "sample_id": "L2301346_rerun"
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "samplesheet_b64gz": "H4sIAIf15mUC/41R0WrCMBT9FcnzhCa1CttTUSgDV4bWhzFGiPZqw5pUk1Qm4r/vJtVtZXsYoZCcc+49veeeSQWiBEPuB2eylTXwbWOUcPwIxspGI87uBsS0mmuhAJ+ksAc9zGG9yFMWU0rj4dMcYFksOB3nzZHFBAukts60CrTj7rQPdciJJRzIxfdDUxs8/Y1TvjltavAIoQklVwVnv3GpS/joF0TfOOvj3srZJomimltwTupd5ypKsXdgeOfu1dMiK6Z4irRIp3jw6tv2hOwfwjVU4iib1idKnJHKk0pqqVrF/VtB2XWrQe9chbI48RJh37mtGuP4LZyAN7gII0v4MdhqktMXOoofHmkUvhvQm7cUTqD69UysUHtcrCx98ZzFEY1HY3TBpfqfu9K3Nc3y1KO10HBdfojWU2mGo6cZDv6VeIik8CFgLGkW8AnvltEZrmbPURSxwCR/Mpe3yyfpAP0IhwIAAA=="  // pragma: allowlist secret
#     # }
