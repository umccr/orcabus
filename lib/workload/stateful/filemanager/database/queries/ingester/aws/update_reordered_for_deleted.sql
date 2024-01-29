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
        s3_object.*
    from s3_object
    -- Grab the correct input point to update with.
    join input on input.s3_object_id = s3_object.s3_object_id
    where
        s3_object.bucket = input.bucket and
        s3_object.key = input.key and
        s3_object.version_id = input.version_id and
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
-- Return the old values because these needs to be reprocessed.
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