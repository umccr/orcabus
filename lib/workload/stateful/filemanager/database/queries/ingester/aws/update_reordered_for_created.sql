-- Update the matching s3_objects which should be re-ordered based on the created event. Returns the
-- data associated with the event before the update, if an update occurred. This is a wrapper around the function
-- of the same name, with some output columns renamed for sqlx.

select
    input_id as "s3_object_id!",
    bucket as "bucket!",
    key as "key!",
    created_date as event_time,
    last_modified_date,
    e_tag,
    storage_class as "storage_class: StorageClass",
    version_id,
    created_sequencer as sequencer,
    number_reordered as "number_reordered!",
    number_duplicate_events as "number_duplicate_events!",
    size,
    -- This is used to simplify re-constructing the FlatS3EventMessages in the Lambda. I.e. this update detected an
    -- out of order created event, so return a created event back.
    'Created' as "event_type!: EventType"
from update_reordered_for_created($1::uuid[], $2::text[], $3::text[], $4::text[], $5::text[], $6::timestamptz[]);