#!/usr/bin/env python3

"""
Generate the payload for the nextflow lambda stack

We have three different payloads to generate depending on the workflow type

DNA -> Given the following inputs

{
    "portal_run_id": "20230515zyxwvuts",
    "subject_id": "SBJ00001",
    "tumor_library_id": "001T",
    "normal_library_id": "001N",
    "tumor_bam_uri": "gds://production/analysis_data/SBJ00001/wgs_tumor_normal/20230515zyxwvuts/001/001T.bam",
    "normal_bam_uri": "gds://production/analysis_data/SBJ00001/wgs_tumor_normal/20230515zyxwvuts/001/001N.bam"
}

Return the following payload

{
  "portal_run_id": "20230515zyxwvuts",
  "subject_id": "SBJ00001",
  "tumor_wgs_sample_id": "001T",
  "tumor_wgs_library_id": "001T",
  "tumor_wgs_bam": "gds://production/analysis_data/SBJ00001/wgs_tumor_normal/20230515zyxwvuts/001/001T.bam",
  "normal_wgs_sample_id": "001T",
  "normal_wgs_library_id": "001N",
  "normal_wgs_bam": "gds://production/analysis_data/SBJ00001/wgs_tumor_normal/20230515zyxwvuts/001/001N.bam"
}

RNA -> Given the following inputs

{
    "portal_run_id": "20230515zyxwvuts",
    "subject_id": "SBJ00001",
    "tumor_library_id": "001T",
    "normal_library_id": "001N",
    "tumor_bam_uri": "gds://production/analysis_data/SBJ00001/wgs_tumor_normal/20230515zyxwvuts/001/001T.bam",
    "normal_bam_uri": "gds://production/analysis_data/SBJ00001/wgs_tumor_normal/20230515zyxwvuts/001/001N.bam"
}

Return the following payload

{
  "portal_run_id": "20230515zyxwvuts",
  "subject_id": "SBJ00001",

}

overrides: {
    "resource_requirements":
    "command":
    "tags":
    "workflow":
    "output":
    "event_data":
}


BOTH -> Given the following inputs
"""



