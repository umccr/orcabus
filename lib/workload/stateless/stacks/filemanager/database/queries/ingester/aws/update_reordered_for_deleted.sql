-- Update the matching s3_objects which should be re-ordered based on the deleted event. Returns the
-- data associated with the event before the update, if an update occurred.

-- First, unnest the input parameters into a query.
with input as (
    select
        *
    from unnest(
        $1::uuid[],
        $2::text[],
        $3::text[],
        $4::timestamptz[],
        $5::text[],
        $6::text[],
        $7::event_type[]
    ) as input (
        s3_object_id,
        bucket,
        key,
        deleted_date,
        version_id,
        deleted_sequencer,
        event_type
    )
),
-- Then, select the objects that match the bucket, key and version_id
current_objects as (
    select
        s3_object.*,
        input.s3_object_id as input_id,
        input.bucket as input_bucket,
        input.key as input_key,
        input.version_id as input_version_id,
        input.deleted_sequencer as input_deleted_sequencer,
        input.deleted_date as input_deleted_date,
        input.event_type as input_event_type
    from s3_object
    -- Grab the relevant values to update with.
    join input on
        input.bucket = s3_object.bucket and
        input.key = s3_object.key and
        input.version_id = s3_object.version_id
    -- Lock this pre-emptively for the update.
    for update
),
-- And filter them to the objects that need to be updated.
objects_to_update as (
    select
        *
    from current_objects
    where
        -- Check the sequencer condition. We only update if there is a deleted
        -- sequencer that is closer to the created sequencer.
        current_objects.sequencer < current_objects.input_deleted_sequencer and
        (
            -- Updating a null sequencer doesn't cause the event to be reprocessed.
            current_objects.deleted_sequencer is null or
            -- If a sequencer already exists this event should be reprocessed because this
            -- sequencer would belong to another object.
            current_objects.deleted_sequencer > current_objects.input_deleted_sequencer
        ) and
        -- And there should not be any objects with a deleted sequencer that is the same as the input deleted
        -- sequencer because this is a duplicate event that would cause a constraint error in the update.
        current_objects.input_deleted_sequencer not in (
            select deleted_sequencer from current_objects where deleted_sequencer is not null
        )
    -- Only one event entry should be updated, and that entry must be the one with the
    -- created sequencer that is maximum, i.e. closest to the deleted sequencer which
    -- is going to be inserted.
    order by current_objects.sequencer desc
    limit 1
),
-- Finally, update the required objects.
update as (
    update s3_object
    set deleted_sequencer = objects_to_update.input_deleted_sequencer,
        deleted_date = objects_to_update.input_deleted_date,
        event_type = objects_to_update.input_event_type,
        number_reordered = s3_object.number_reordered +
            case when objects_to_update.deleted_sequencer is null then 0 else 1 end
    from objects_to_update
    where s3_object.s3_object_id = objects_to_update.s3_object_id
)
-- Return the old values because these need to be reprocessed.
select
    -- Note, this is the passed through value from the input in order to identify this event later.
    input_id as "s3_object_id",
    bucket,
    key,
    deleted_date as event_time,
    last_modified_date,
    e_tag,
    sha256,
    storage_class,
    version_id,
    deleted_sequencer as sequencer,
    number_reordered,
    number_duplicate_events,
    size,
    is_delete_marker,
    ingest_id,
    reason,
    archive_status,
    is_current_state,
    attributes,
    -- This is used to simplify re-constructing the FlatS3EventMessages in the Lambda. I.e. this update detected an
    -- out of order deleted event, so return a deleted event back.
    'Deleted'::event_type as "event_type"
from objects_to_update;
