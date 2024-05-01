#!/usr/bin/env python3

ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

# External Portal SSM Path
PORTAL_API_BASE_URL_SSM_PATH = "/data_portal/backend/api_domain_name"
PORTAL_METADATA_ENDPOINT = "https://{PORTAL_API_BASE_URL}/iam/metadata/"

# FIXME - should be an input parameter to the state machine
ICAV2_CACHE_PROJECT_ID_SSM_PATH = "/icav2/umccr-prod/cache_project_id"
ICAV2_CACHE_PROJECT_BCLCONVERT_OUTPUT_SSM_PATH = "/icav2/umccr-prod/cache_project_bclconvert_output_path"


ICAV2_CACHE_PROJECT_CTTSO_OUTPUT_SSM_PATH = "/icav2/umccr-prod/cache_project_cttso_fastq_path"
