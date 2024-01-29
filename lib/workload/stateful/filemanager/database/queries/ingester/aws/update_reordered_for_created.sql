-- Update the matching s3_objects which should be re-ordered based on the created event. Returns the
-- data associated with the event before the update, if an update occurred.

-- First, unnest the input parameters into a query.
with input as (
    select
        *
    from unnest($1::text[], $2::text[], $3::text[], $4::text[], $5::timestamptz[]) as input (
        bucket,
        key,
        version_id,
        created_sequencer,
        created_date
    )
),
-- Then, select the objects that need to be updated.
current_s3_objects as (
    select
        s3_object.*
    from s3_object
        -- Grab the relevant values to update with.
        join input on
        input.bucket = s3_object.bucket and
        input.key = s3_object.key and
        input.version_id = s3_object.version_id
    where
        -- Check the sequencer condition. We only update if there is a created
        -- sequencer that is closer to the deleted sequencer.
        s3_object.deleted_sequencer > input.created_sequencer and
        (
            s3_object.created_sequencer is null or
            s3_object.created_sequencer < input.created_sequencer
        )
    -- Lock this pre-emptively for the update.
    for update
),
-- Finally, update the required objects.
update as (
    update s3_object
    set created_sequencer = current_s3_objects.created_sequencer,
        created_date = current_s3_objects.created_date,
        number_reordered = s3_object.number_reordered + 1
    from current_s3_objects
    where s3_object.s3_object_id = current_s3_objects.s3_object_id
)
-- Return the old values because these need to be reprocessed.
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
from current_s3_objects;