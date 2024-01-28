-- Update the deleted time of objects.
update s3_object
set deleted_date = data.deleted_time,
    deleted_sequencer = data.deleted_sequencer
from (select
    unnest($1::text[]) as key,
    unnest($2::text[]) as bucket,
    unnest($3::timestamptz[]) as deleted_time,
    unnest($4::text[]) as deleted_sequencer
) as data
    where s3_object.key = data.key and s3_object.bucket = data.bucket;
