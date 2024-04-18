#!/usr/bin/env python3

"""
From a b64 compression json, generate a samplesheet

{
    "samplesheet_b64gz": ""
}

Returns

{
    "samplesheet_str": ""
}

"""
from typing import Dict

from v2_samplesheet_maker.functions.v2_samplesheet_writer import v2_samplesheet_writer
from pieriandx_pipeline_tools.utils.compression_helpers import decompress_dict


def handler(event, context) -> Dict[str, str]:
    # Get b64gz string
    samplesheet_b64gz = event.get("samplesheet_b64gz", None)

    # Decompress dict
    samplesheet_dict = decompress_dict(samplesheet_b64gz)

    # Convert to string
    samplesheet_str = str(v2_samplesheet_writer(samplesheet_dict).read())

    # Replace TSO500L_Data header line
    # Sample_ID,Sample_Type,Lane,Index,Index2,I7_Index_ID,I5_Index_ID
    # With
    # Sample_ID,Sample_Type,Lane,index,index2,I7_Index_ID,I5_Index_ID
    # Without changing the Index1Cycles and Index2Cycles of the Reads section
    # Hacky and dirty workaround required because PierianDx is not able to handle Index / Index2 in uppercase
    # Assumes Index and Index2 fall within the middle of the index line
    samplesheet_str = samplesheet_str.replace(',Index', ',index')

    return {
        "samplesheet_str": samplesheet_str
    }


# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "samplesheet_b64gz": "H4sIAAAAAAAAA42SX0vDMBTF3/cpRp4VktY5/zyFCUXQIto9iEjI7N0abNItyYZj7Lt7065rh3uQ0tLc37npybndDYZDUoDMwZK74Q5XuJ6rEsS8slp6sQHrVGUQRhcNtWsjjNSAJZK5lblMYfaa8ihmjMWXz08Ab9mrYNdptYlicmhSxnm71mC88Ntl3YtcvsGKoGAfVMSiDde5CEvBxNf2q4RQZiN20SPROaJMDj8nTfSE9Jvo8cPeVSNKS+HAe2UWPQ8yl0sPVjRegutJlmQTvDKe8Qle+Nqe8UQc/VM8g0JuVLUO8RNvlW4FWhml11qEmoa82bUEs/AFSuNRK5PuW7iisl60+R1ZhcOzKofu0GQ6Ttk7u4rvHxmt77ZA/qSRSy+x5aPeq8kDqZN6iX+HysNuT1FMWXx9c/Dc4XbGDynvWClNKLJjoZ5JkCUck+JJxhNyCpsUkWJ0nE96dCyaiTZGpg8vlNLbHh+d5TXe4/NzsB/8AvJdybj8AgAA"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
# # Yields
# # {
# #   "samplesheet_str": "[Header]\nFileFormatVersion,2\nRunName,Tsqn-NebRNA231113-MLeeSTR_16Nov23\nInstrumentType,NovaSeq\n\n[Reads]\nRead1Cycles,151\nRead2Cycles,151\nIndex1Cycles,10\nIndex2Cycles,10\n\n[TSO500L_Settings]\nAdapterRead1,CTGTCTCTTATACACATCT\nAdapterRead2,CTGTCTCTTATACACATCT\nAdapterBehaviour,trim\nMinimumTrimmedReadLength,35\nMaskShortReads,35\nOverrideCycles,U7N1Y143;I10;I10;U7N1Y143\n\n[TSO500L_Data]\nSample_ID,Sample_Type,Lane,Index,Index2,I7_Index_ID,I5_Index_ID\nL2301368,DNA,1,GACTGAGTAG,CACTATCAAC,UDP0009,UDP0009\n"
# # }

