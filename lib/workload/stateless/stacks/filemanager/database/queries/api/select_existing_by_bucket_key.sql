-- Select the most recent s3_objects based on the input bucket, key and version_id values
-- into FlatS3EventMessage structs. This query effectively fetches the current state of the
-- database objects in S3 for a set of buckets, keys and version_ids, using `is_current_state`.
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
    event_time,
    last_modified_date,
    e_tag,
    sha256,
    storage_class,
    s3_object.version_id,
    sequencer,
    number_duplicate_events,
    size,
    is_delete_marker,
    reason,
    archive_status,
    event_type,
    ingest_id,
    attributes,
    is_current_state,
    0::bigint as "number_reordered"
from input
-- Grab the most recent object in each input group.
cross join lateral (
    -- Cross join the input with one s3_object based on the most recent event.
    select
        *
    from s3_object
    where
        input.bucket = s3_object.bucket and
        input.key = s3_object.key and
        input.version_id = s3_object.version_id and
        s3_object.is_current_state = true
    order by s3_object.sequencer desc nulls last
    limit 1
)
as s3_object
for update;
