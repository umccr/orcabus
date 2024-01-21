-- Update the deleted time of objects.
update s3_object
set deleted_date = data.deleted_time
from (select
    unnest($1::varchar[]) as key,
    unnest($2::varchar[]) as bucket,
    unnest($3::timestamptz[]) as deleted_time
) as data
where s3_object.key = data.key and s3_object.bucket = data.bucket;
