-- Update the matching s3_object which should be re-ordered based on the deleted event. Returns the
-- data associated with the event before the update, if an update occurred.
with current_s3_object as (
    select
        s3_object_id,
        object_id,
        bucket,
        key,
        created_date,
        deleted_date,
        last_modified_date,
        e_tag,
        storage_class,
        version_id,
        created_sequencer,
        deleted_sequencer,
        number_reordered,
        number_duplicate_events
    from s3_object where
        s3_object.bucket = $1::text and
        s3_object.key = $2::text and
        s3_object.version_id = $3::text and
        s3_object.created_sequencer < $4::text and
        (
           s3_object.deleted_sequencer is null or
           s3_object.deleted_sequencer > $4::text
        )
    -- Lock this pre-emptively for the update.
    for update
), update as (
    update s3_object
    set deleted_sequencer = $4::text,
        deleted_date = $5::timestamptz,
        number_reordered = number_reordered + 1
    -- Only expecting one or no values here.
    where object_id in (select object_id from current_s3_object)
)
-- Return the old value because this needs to be reprocessed.
select
    s3_object_id as "s3_object_id!",
    object_id as "object_id!",
    bucket,
    key,
    created_date,
    deleted_date,
    last_modified_date,
    e_tag,
    storage_class as "storage_class: StorageClass",
    version_id,
    created_sequencer,
    deleted_sequencer,
    number_reordered,
    number_duplicate_events
from current_s3_object;