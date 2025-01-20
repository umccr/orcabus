/*
We generate some lambda functions that allow the api endpoint to
query other services.
*/

export const LAMBDA_HELPER_FUNCTION_NAMES = [
  'get_library_orcabus_id_from_library_id_fastq_manager',
  'get_library_id_from_library_orcabus_id_fastq_manager',
  'get_presigned_url_from_s3_uri_fastq_manager',
  'get_s3_ingest_id_from_s3_uri_fastq_manager',
  'get_s3_uri_from_s3_ingest_id_fastq_manager',
];
