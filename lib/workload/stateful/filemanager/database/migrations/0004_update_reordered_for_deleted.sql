-- Update the matching s3_objects which should be re-ordered based on the deleted event. Returns the
-- data associated with the event before the update, if an update occurred.
create or replace function update_reordered_for_deleted(
    s3_object_ids uuid[],
    buckets text[],
    keys text[],
    version_ids text[],
    deleted_sequencers text[],
    deleted_dates timestamptz[]
) returns table (
    input_id uuid,
    bucket text,
    key text,
    deleted_date timestamptz,
    last_modified_date timestamptz,
    e_tag text,
    storage_class storage_class,
    version_id text,
    deleted_sequencer text,
    number_reordered integer,
    number_duplicate_events integer,
    size integer
) as $$
    begin
        create temp table current_s3_objects on commit drop as
        -- First, unnest the input parameters into a record.
        with input as (
            select
                *
            from unnest(s3_object_ids, buckets, keys, version_ids, deleted_sequencers, deleted_dates) as input (
                s3_object_id,
                bucket,
                key,
                version_id,
                deleted_sequencer,
                deleted_date
            )
        )
        -- Then, select the objects that need to be updated.
        select
            s3_object.*,
            input.s3_object_id as input_id,
            input.bucket as input_bucket,
            input.key as input_key,
            input.version_id as input_version_id,
            input.deleted_sequencer as input_deleted_sequencer,
            input.deleted_date as input_deleted_date
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
                -- Updating a null sequencer doesn't cause the event to be reprocessed.
                s3_object.deleted_sequencer is null or
                -- If a sequencer already exists this event should be reprocessed because this
                -- sequencer would belong to another object.
                s3_object.deleted_sequencer > input.deleted_sequencer
            )
        -- Lock this pre-emptively for the update.
        for update;

        -- Finally, update the required objects.
        update s3_object
        set deleted_sequencer = current_s3_objects.input_deleted_sequencer,
            deleted_date = current_s3_objects.input_deleted_date,
            number_reordered = s3_object.number_reordered +
                -- If the sequencer is null then this isn't a reorder, so it shouldn't add to the counter.
                case when current_s3_objects.deleted_sequencer is null then 0 else 1 end
        from current_s3_objects
        where s3_object.s3_object_id = current_s3_objects.s3_object_id;

        -- Return the old values because these need to be reprocessed.
        return query
        select
            -- Note, this is the passed through value from the input in order to identify this event later.
            current_s3_objects.input_id,
            current_s3_objects.bucket,
            current_s3_objects.key,
            current_s3_objects.deleted_date,
            current_s3_objects.last_modified_date,
            current_s3_objects.e_tag,
            current_s3_objects.storage_class,
            current_s3_objects.version_id,
            current_s3_objects.deleted_sequencer,
            current_s3_objects.number_reordered,
            current_s3_objects.number_duplicate_events,
            -- Also need the size from the object table.
            object.size
        from current_s3_objects
        join object on object.object_id = current_s3_objects.object_id;
    end;
$$ language plpgsql;