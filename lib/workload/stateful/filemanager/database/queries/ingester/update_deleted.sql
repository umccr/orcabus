-- Update the deleted time of s3 objects.
update object
set deleted_date = data.deleted_time
from (select
    unnest($1::varchar[]) as key,
    unnest($2::varchar[]) as bucket,
    unnest($3::timestamptz[]) as deleted_time
) as data
where object.key = data.key and object.bucket = data.bucket;