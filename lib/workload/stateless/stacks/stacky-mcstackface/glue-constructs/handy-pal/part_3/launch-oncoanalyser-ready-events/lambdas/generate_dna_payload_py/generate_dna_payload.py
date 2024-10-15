#!/usr/bin/env python3

"""
Generate a DNA payload for the oncoanalyser event

{
   "inputs": {
     "mode": "wgts | targeted"
     "analysis_type": "DNA | RNA | DNA/RNA"
     "subject_id": "<subject_id>", // Required
     "tumor_dna_sample_id": "<tumor_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "normal_dna_sample_id": "<normal_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "tumor_dna_bam_uri": "<tumor_bam_uri>",  // Required if analysis_type is set to DNA
     "normal_dna_bam_uri": "<normal_bam_uri>",  // Required if analysis_type is set to DNA
   },
   "engine_parameters": {
     "portal_run_id": "<portal_run_id>",  // Always required
     "output_results_dir": "<output_results_dir>",  // Always required
     "output_staging_dir": "<output_staging_dir>",  // Always required
     "output_scratch_dir": "<output_scratch_dir>",  // Always required
     "custom_config_str":  "<custom_config_str>"  // Optional
     "resume_nextflow_uri": "<resume_nextflow_uri>"  // Optional
     "pipeline_version": "<pipeline_version>"  // Optional
   },
   "tags": {
      "tumorDnaLibraryId": "<tumor_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "normalDnaLibraryId": "<normal_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "tumorRnaLibraryId": "<rna_sample_id>", // Present if analysis_type is set to RNA
      "subjectId": "<subject_id>",
      "individualId": "<individual_id>",
   }
}

"""