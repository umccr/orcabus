-- Update the matching s3_objects which should be re-ordered based on the created event. Returns the
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
        $5::bigint[],
        $6::text[],
        $7::timestamptz[],
        $8::text[],
        $9::storage_class[],
        $10::text[],
        $11::text[],
        $12::boolean[]
    ) as input (
        s3_object_id,
        bucket,
        key,
        created_date,
        size,
        sha256,
        last_modified_date,
        e_tag,
        storage_class,
        version_id,
        created_sequencer,
        is_delete_marker
    )
),
-- Then, select the objects that need to be updated.
current_objects as (
    select
        s3_object.*,
        input.s3_object_id as input_id,
        input.bucket as input_bucket,
        input.key as input_key,
        input.version_id as input_version_id,
        input.created_sequencer as input_created_sequencer,
        input.created_date as input_created_date,
        input.size as input_size,
        input.sha256 as input_sha256,
        input.last_modified_date as input_last_modified_date,
        input.e_tag as input_e_tag,
        input.storage_class as input_storage_class,
        input.is_delete_marker as input_is_delete_marker
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
        -- Check the sequencer condition. We only update if there is a created
        -- sequencer that is closer to the deleted sequencer.
        current_objects.deleted_sequencer > current_objects.input_created_sequencer and
        (
            -- Updating a null sequencer doesn't cause the event to be reprocessed.
            current_objects.created_sequencer is null or
            -- If a sequencer already exists this event should be reprocessed because this
            -- sequencer could belong to another object.
            current_objects.created_sequencer < current_objects.input_created_sequencer
        ) and
        -- And there should not be any objects with a created sequencer that is the same as the input created
        -- sequencer because this is a duplicate event that would cause a constraint error in the update.
        current_objects.input_created_sequencer not in (
            select created_sequencer from current_objects where created_sequencer is not null
        )
    -- Only one event entry should be updated, and that entry must be the one with the
    -- deleted sequencer that is minimum, i.e. closest to the created sequencer which
    -- is going to be inserted.
    order by current_objects.deleted_sequencer asc
    limit 1
),
-- Finally, update the required objects.
update as (
    update s3_object
    set created_sequencer = objects_to_update.input_created_sequencer,
        created_date = objects_to_update.input_created_date,
        size = objects_to_update.input_size,
        sha256 = objects_to_update.input_sha256,
        last_modified_date = objects_to_update.input_last_modified_date,
        e_tag = objects_to_update.input_e_tag,
        is_delete_marker = objects_to_update.input_is_delete_marker,
        storage_class = objects_to_update.input_storage_class,
        number_reordered = s3_object.number_reordered +
            -- Note the asymmetry between this and the reorder for deleted query.
            case when objects_to_update.deleted_sequencer is not null or objects_to_update.created_sequencer is not null then
                1
            else
                0
            end
    from objects_to_update
    where s3_object.s3_object_id = objects_to_update.s3_object_id
)
-- Return the old values because these need to be reprocessed.
select
    -- Note, this is the passed through value from the input in order to identify this event later.
    input_id as "s3_object_id!",
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
    is_delete_marker,
    -- This is used to simplify re-constructing the FlatS3EventMessages in the Lambda. I.e. this update detected an
    -- out of order created event, so return a created event back.
    'Created' as "event_type!: EventType"
from objects_to_update;
