alter table s3_object add column ingest_id uuid;
create index ingest_id_index on s3_object (ingest_id);
