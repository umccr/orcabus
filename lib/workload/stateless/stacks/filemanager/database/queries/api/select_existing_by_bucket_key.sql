-- Select the existing and most recent s3_objects (those that haven't yet been deleted)
-- based on the input bucket, key and version_id values into FlatS3EventMessage structs.
-- This query effectively fetches the current objects in S3 for a set of buckets, keys
-- and version_ids.
-- TODO, potentially replace this with sea-orm codegen and query builder.

-- Unnest input.
with input as (
    select
        *
    from unnest(
        $1::text[],
        $2::text[],
        $3::text[]
    ) as input (
        bucket,
        key,
        version_id
    )
)
-- Select objects into a FlatS3EventMessage struct.
select
    s3_object_id,
    s3_object.bucket,
    s3_object.key,
    created_date as event_time,
    last_modified_date,
    e_tag,
    sha256,
    storage_class as "storage_class?: StorageClass",
    s3_object.version_id as "version_id!",
    created_sequencer as sequencer,
    number_reordered,
    number_duplicate_events,
    size,
    'Created' as "event_type!: EventType"
from input
-- Grab the most recent object in each input group.
cross join lateral (
    -- Cross join the input with one s3_object based on the most recent created_date.
    select
        *
    from s3_object
    where
        input.bucket = s3_object.bucket and
        input.key = s3_object.key and
        input.version_id = s3_object.version_id
    order by s3_object.created_date desc
    limit 1
)
as s3_object
for update;
