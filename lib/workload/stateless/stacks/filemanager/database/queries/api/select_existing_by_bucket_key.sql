-- Select the existing and most recent s3_object (those that haven't yet been deleted)
-- based on the input bucket, key and version_id values.

select
    s3_object_id,
    bucket,
    key,
    created_date as event_time,
    last_modified_date,
    e_tag,
    sha256,
    storage_class as "storage_class?: StorageClass",
    version_id as "version_id!",
    created_sequencer as sequencer,
    number_reordered,
    number_duplicate_events,
    size,
    -- Since this object hasn't been deleted, the corresponding event is a created event.
    'Created' as "event_type!: EventType"
from s3_object where
    bucket = $1 and
    key = $2 and
    version_id = $3 and
    deleted_sequencer is null
order by last_modified_date desc
limit 1