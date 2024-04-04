#!/usr/bin/env python3

"""
Given a cache path, sample id and list of fastq list rows,
generate a manifest file to copy fastq files to the cache directory

This will be launched in a downstream step

Given

{
    "cache_uri": "/path/to/cache",
    "sample_id": "sample_id",
    "fastq_list_rows": [ { "RGID": "...", "RGLB": "...", "RGSM": "sample_id", "Read1FileURI": "icav2://", "...", "Read1FileURISrc": "icav2://"} ]
    /* Except fastq list rows is b64gz encoded */
}

Return a manifest list

{
    "manifest_list": [
      {
        "fastq_list_rows[0].Read1FileURI": [  # trial
            "cache_uri",  # dest_uri
        ],
        "fastq_list_rows[0].Read2FileURI": [  # trial
            "cache_uri",  # dest_uri
        ],
        ...
      }
    ]
}
"""
from functools import reduce
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from wrapica.enums import DataType
from wrapica.project_data import convert_project_id_and_data_path_to_icav2_uri

from cttso_v2_pipeline_manager_tools.utils.compression_helpers import decompress_dict


def handler(event, context):
    """

    Generate a copy manifest from fastq list rows to cache path

    Args:
        event:
        context:

    Returns:

    """

    # Get the cache path
    cache_uri = event.get("cache_uri", None)
    # Check cache path
    if cache_uri is None:
        raise ValueError("Cache uri is required")

    project_id = urlparse(cache_uri).netloc
    cache_path = Path(urlparse(cache_uri).path)

    # Get sample id
    sample_id = event.get("sample_id", None)

    # Get fastq list rows
    fastq_list_rows_compressed_str = event.get("fastq_list_rows_b64gz", None)

    # Check sample id
    if sample_id is None:
        raise ValueError("Sample id is required")

    # Check fastq list rows
    if fastq_list_rows_compressed_str is None:
        raise ValueError("Fastq list rows are required")

    # Uncompress fastq list rows
    fastq_list_rows: List[Dict] = decompress_dict(fastq_list_rows_compressed_str)

    # Generate the manifest list
    fastq_cache_path = convert_project_id_and_data_path_to_icav2_uri(
        project_id=project_id,
        data_path=Path(cache_path) / sample_id,
        data_type=DataType.FOLDER
    )

    # Filter fastq list rows by RGSM (match sample_id)
    fastq_list_rows = list(
        filter(
            lambda fastq_list_row_iter: fastq_list_row_iter.get("RGSM") == sample_id,
            fastq_list_rows
        )
    )

    # Generate source uris
    source_uris = list(
        reduce(
            # Flatten the list
            lambda row_iter_1, row_iter_2: row_iter_1 + row_iter_2,
            map(
                lambda fastq_list_row_iter: [
                    fastq_list_row_iter.get("Read1FileURI"),
                    fastq_list_row_iter.get("Read2FileURI")
                ],
                fastq_list_rows
            )
        )
    )

    # Generate the manifest list
    manifest_list = dict(
        map(
            lambda source_uri_iter: (
                source_uri_iter,
                [
                    fastq_cache_path
                ]
            ),
            source_uris
        )
    )

    # Return the manifest list
    return {
        "manifest_list": manifest_list
    }


# if __name__ == "__main__":
#
#     import json
#
#     fastq_list_rows_b64gz = """
# H4sIALln6WUC/+Wd32/cNgzH/5Ugz7XPkvyzb66LaQXSl9odBgyD4fO5Q7Dk0l3TDt2w/32kstOtKatLlL7wiD6UTg64fsl+LIqm6F/+Pn9jX708f352bt
# tusK0dWpt2YLZD17Zdqs6fncFH+tf4kQttMmXK+u5nFy/wZ2+3v29v/txeXK530+4z/uZi2i7wG4UfWqaN+uHyann75lW/m/Hzl/P0ST9frdbavFsXqkw2
# daGTvKmLZNrMc1IbNSu91PNG69Xl1fU2mbbT1ecPy4eVNkqpcmwzlRV6zFSlxxc//nTxunjZ/1yNG52XhRrzuck2c/Jivuputp+W3e3Zp3zUY5WsK9XM9a
# ZJiqXcwBcuZTLV6yWZJ1Wti6XZ5Nl6dfPx9v3H21U/Xb+/gm9EKaNa7XV7Y+zVeJFlanyjRvgrfTd9uP0j/e2v8/8065PWrEnN+zj/X3BVNMVSv9OJ0RuT
# 5HMF3290nszlVBebaanhX+EEj+93l9fw/2elM23ColemLFVZNPjRPDNZNa3nTVU32XeLGgcF92Lwz7OzA8kAcdcCzrZNBzAtcG0HkuRGKMmNN8ZeCyGZ0s
# yL5MdHjYOCEMldB+sxMDx0aQtID+6KIrnKZJJcZd4YeyODZFIzK5IjosZBQYhk6xZlSK5t2lpYkiHFprPrSgkl+WCMfS6EZEozL5IfHzUOCoJr8jAgvsPQ
# ph3YsELblsyuKy2UZO2NsS+EkExp5kXy46PGQUF4Tcal2OJC7OpecNXR2bURSrLxxtiXQkimNPMi+fFR46AgXPG6K3nBmoyF62FwZWz9Ncl5Oe6W3cftg3
# jWp8Lz/sa4V3/vcuwr9LE+WbYfrJ8F598pmtzUBHNywN9trwfcXQ/u8VVL8l+J5r/60sfV3se1EP6P6efF/9OiyU1NcP2HfTjij8+uIZ2HVACyepL/WjT/
# 9Zc+rvc+boTwf0w/L/6fFk1uasI7+c5i+g+LPqCPNwLYAZD8N6L5b770cbP3scqE3ACOOoDXHeCJ8WQnJ5gDtJABdPhsDZ+V48NyuCtQ94Aik3wP2Ku/dw
# lOVjLuAccdwOoe8NR4spMTuge4XcDgyvjuwRxekfeAKpdJf5V7A1yqZRBPi2ZFeUzcWEgIV/UsZPT4hC51BT0s8pFZfVUIpbnwBrjUCKGZFM2L5oi4sZBw
# pAMOT5S0Ka7KWKOnSK6FklwX3gB35jJIpkWzIjkmbiwkhHfaWGqzQDIeLIFEmyS5Ekpy5Q1wZyGEZFI0L5Ij4sZCQjDDxjIZZNipdZ1wQ5saguTyQSSbUy
# F533xUl94Ad7o2JHOyJIdFsyD5KXFjISGYXQ/4B7bHFnPs9hsk10JJrr0B7qyEkEyK5kVyRNxYSAjWsF1Puh1S2CLjU21LktwIJbnxBrizFkIyKZoXyRFx
# YyEhnF1jI0rbpR3WsWFhpkhuMpkkN5k3wJ2NDJJp0axIjokbCwnh2vXgJiJhd7lrNCdJVkJJVt4Ye50JIZkUzYvkiLixkBA+Kda5iUgplrA7yLVJkrVQkr
# U3wJ1KCMmkaF4kR8SNhYQj3SEtjix0nV5YxyZJNkJJPhjgTi2EZFI0L5Ij4sZCQrDihR2beGB7uGvbprPrQijJhTfAnUYIyaRoXiRHxI2FhCPzCl3TJvZr
# Wpdm51+TrB+2T85PheR936tW3gB3ukab/GRJDotmQfJT4sZCQnhNxuJ112F23brSF0WyFkqy9ga4sxBCMimaF8kRcWMhIVi7xsH+kFWnbkgKrMokyUYoyc
# Yb4M5SCMmkaF4kR8SNhYQjfdd4wBFnnN1NOyJJzoWSfDDAnZUQkknRvEiOiBsLCeF5RTimaLBp2+H40W/skwuhJBfeAHfWQkgmRfMiOSJuLCQEs2s3bBRP
# Ne5f1EGRXAolufQGuLMRQjIpmhfJEXFjISHcrelGh+I+uXMskyRXQkmuvDH2JhNCMimaF8kRcWMhIXyCAvs17d0scDfenyK5Fkpy7Q1wpxJCMimaF8kRcW
# Mh4cibLHGuP/Z4YXJt6dp1I5TkxhvgTi2EZFI0L5Ij4sZCwpEJvfh66TbFyrUrYhMkm0wmySbzBrjTyCCZFs2K5Ji4sZAQnrHppnfdTRrovvE82Qjt8TLK
# G+BOIT1etGheJEfEjYWE8Jss8SyUO9VoXb8XSbLQHi+jvQHuFNLjRYvmRXJE3FhICK7Jbs5Aa3EiX+teg0WRLLTHyxhvgDuF9HjRonmRHBE3FhKOnGp0b5
# TGd1hY9zILimShPV7mYIA7hfR40aJ5kRwRNxYSwj1e1p1nTLFT07b082QjtMfLFN4Adwrp8aJF8yI5Im4sJIT7rocOpw2kbt4AtogQJOdC1+T8YIA7hfR4
# 0aJZkRwTNxYSHjdbM4+erXlyJBMDDk+fZFo0K5Jj4sZCwuMm8uXRE/lOjmRiLNrpk0yLZkVyTNxYSDhSu7buBAU+Vbb4giiKZKHZdXMwxj6XQjIpmhfJEX
# FjIeE+yb/+C4TOMeRCoAAA
# """.replace("\n", "")
#
#     # Test the handler
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "cache_path": "/ilmn_cttso_fastq_cache/20241231abcd1234/L12345678_run_cache",
#                     "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
#                     "sample_id": "L2301346_rerun",
#                     "fastq_list_rows_b64gz": fastq_list_rows_b64gz
#                 },
#                 context=None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "manifest_list": {
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_2/L2301346_rerun/L2301346_rerun_S7_L002_R1_001.fastq.gz": [
#     #             "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20241231abcd1234/L12345678_run_cache/L2301346_rerun/"
#     #         ],
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_2/L2301346_rerun/L2301346_rerun_S7_L002_R2_001.fastq.gz": [
#     #             "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20241231abcd1234/L12345678_run_cache/L2301346_rerun/"
#     #         ]
#     #     }
#     # }