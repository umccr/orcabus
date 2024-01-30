-- Update the matching s3_objects which should be re-ordered based on the deleted event. Returns the
-- data associated with the event before the update, if an update occurred.

-- First, unnest the input parameters into a query.
with input as (
    select
        *
    from unnest($1::uuid[], $2::text[], $3::text[], $4::text[], $5::text[], $6::timestamptz[]) as input (
        s3_object_id,
        bucket,
        key,
        version_id,
        deleted_sequencer,
        deleted_date
    )
),
-- Then, select the objects that need to be updated.
current_s3_objects as (
    select
        s3_object.*,
        -- Pass this through to the output.
        input.s3_object_id as input_id
    from s3_object
    -- Grab the relevant values to update with.
    join input on
        input.bucket = s3_object.bucket and
        input.key = s3_object.key and
        input.version_id = s3_object.version_id
    where
        -- Check the sequencer condition. We only update if there is a deleted
        -- sequencer that is closer to the created sequencer.
        s3_object.created_sequencer < input.deleted_sequencer and
        (
            s3_object.deleted_sequencer is null or
            s3_object.deleted_sequencer > input.deleted_sequencer
        )
    -- Lock this pre-emptively for the update.
    for update
),
-- Finally, update the required objects.
update as (
    update s3_object
    set deleted_sequencer = current_s3_objects.deleted_sequencer,
        deleted_date = current_s3_objects.deleted_date,
        number_reordered = s3_object.number_reordered + 1
    from current_s3_objects
    where s3_object.s3_object_id = current_s3_objects.s3_object_id
)
-- Return the old values because these need to be reprocessed.
select
    -- Note, this is the passed through value from the input in order to identify this event later.
    input_id as "s3_object_id!",
    bucket,
    key,
    deleted_date as event_time,
    last_modified_date,
    e_tag,
    storage_class as "storage_class: StorageClass",
    version_id,
    deleted_sequencer as sequencer,
    number_reordered,
    number_duplicate_events,
    -- Also need the size from the object table.
    size,
    -- This is used to simplify re-constructing the FlatS3EventMesssages in the Lambda. I.e. this update detected an
    -- out of order deleted event, so return a deleted event back.
    'Removed' as "event_type!: EventType"
from current_s3_objects
join object on object.object_id = current_s3_objects.object_id;