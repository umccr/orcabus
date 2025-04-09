#!/usr/bin/env bash

set -euo pipefail

# Assert that VIRTUAL_ENV env var is set
if [[ -z "${VIRTUAL_ENV-}" ]]; then
    echo "VIRTUAL_ENV env var is not set. Exiting..."
    exit 1
fi

# Ensure we have the right environment variables
if [[ -z "${JOB_ID-}" ]]; then
    echo "JOB_ID env var is not set. Exiting..."
    exit 1
fi

# Ensure we have the right package name
if [[ -z "${PACKAGE_NAME-}" ]]; then
    echo "PACKAGE_NAME env var is not set. Exiting..."
    exit 1
fi

# Ensure we have the right output uri
if [[ -z "${OUTPUT_URI-}" ]]; then
    echo "OUTPUT_URI env var is not set. Exiting..."
    exit 1
fi

# Generate the rmarkdown template
uv run generate_data_summary_report_template.py

# Run the rmarkdown report
Rscript -e "rmarkdown::render('data_summary_report.Rmd', output_file = 'data_summary_report.html')"

# Upload the report to the S3 bucket
aws s3 cp data_summary_report.html "${OUTPUT_URI}"
