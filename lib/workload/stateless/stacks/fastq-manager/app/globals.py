#!/usr/bin/env python3

import re

ORCABUS_ULID_REGEX_MATCH = re.compile(r'^[a-z0-9]{3}\.[A-Z0-9]{27}$')
GET_LIBRARY_ORCABUS_ID_FROM_LIBRARY_ID_LAMBDA_FUNCTION_NAME = 'get_library_orcabus_id_from_library_id_fastq_manager'
GET_LIBRARY_ID_FROM_LIBRARY_ORCABUS_ID_LAMBDA_FUNCTION_NAME = 'get_library_id_from_library_orcabus_id_fastq_manager'
GET_PRESIGNED_URL_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_NAME = 'get_presigned_url_from_s3_uri_fastq_manager'
GET_S3_INGEST_ID_FROM_S3_URI_LAMBDA_FUNCTION_NAME = 'get_s3_ingest_id_from_s3_uri_fastq_manager'
GET_S3_URI_FROM_S3_INGEST_ID_LAMBDA_FUNCTION_NAME = 'get_s3_uri_from_s3_ingest_id_fastq_manager'