-- Update the deleted time of s3 objects.
update object
set deleted_date = data.deleted_time
from
    (select unnest(?) as key, unnest(?) as bucket, unnest(?) as deleted_time) as data
where object.key = data.key and object.bucket = data.bucket;