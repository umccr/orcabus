-- Update the matching s3_objects which should be re-ordered based on the created event. Returns the
-- data associated with the event before the update, if an update occurred.
create or replace function update_reordered_for_created(
    s3_object_ids uuid[],
    buckets text[],
    keys text[],
    version_ids text[],
    created_sequencers text[],
    created_dates timestamptz[]
) returns table (
    input_id uuid,
    bucket text,
    key text,
    created_date timestamptz,
    last_modified_date timestamptz,
    e_tag text,
    storage_class storage_class,
    version_id text,
    created_sequencer text,
    number_reordered integer,
    number_duplicate_events integer,
    size integer
) as $$
    declare
        current_name text;
        constraint_name text := 'created_sequencer_unique';
    begin
        create temp table current_s3_objects on commit drop as
        -- First, unnest the input parameters into a record.
        with input as (
            select
                *
            from unnest(s3_object_ids, buckets, keys, version_ids, created_sequencers, created_dates) as input (
                s3_object_id,
                bucket,
                key,
                version_id,
                created_sequencer,
                created_date
            )
        )
        -- Then, select the objects that need to be updated.
        select
            s3_object.*,
            input.s3_object_id as input_id,
            input.bucket as input_bucket,
            input.key as input_key,
            input.version_id as input_version_id,
            input.created_sequencer as input_created_sequencer,
            input.created_date as input_created_date
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
                -- Updating a null sequencer doesn't cause the event to be reprocessed.
                s3_object.created_sequencer is null or
                -- If a sequencer already exists this event should be reprocessed because this
                -- sequencer could belong to another object.
                s3_object.created_sequencer < input.created_sequencer
            )
        -- Lock this pre-emptively for the update.
        for update;

        begin
            -- Finally, update the required objects.
            update s3_object
            set created_sequencer = current_s3_objects.input_created_sequencer,
                created_date = current_s3_objects.input_created_date,
                number_reordered = s3_object.number_reordered +
                    -- If the sequencer is null then this isn't a reorder, so it shouldn't add to the counter.
                                   case when current_s3_objects.created_sequencer is null then 0 else 1 end
            from current_s3_objects
            where s3_object.s3_object_id = current_s3_objects.s3_object_id;
        exception when unique_violation then
            get stacked diagnostics current_name := constraint_name;
            -- If the exception matches the constraint name, this is okay, as it's a duplicate that will be
            -- handled later.
            if current_name != constraint_name then
                raise;
            end if;
        end;

        -- Return the old values because these need to be reprocessed.
        return query
        select
            -- Note, this is the passed through value from the input in order to identify this event later.
            current_s3_objects.input_id,
            current_s3_objects.bucket,
            current_s3_objects.key,
            current_s3_objects.created_date,
            current_s3_objects.last_modified_date,
            current_s3_objects.e_tag,
            current_s3_objects.storage_class,
            current_s3_objects.version_id,
            current_s3_objects.created_sequencer,
            current_s3_objects.number_reordered,
            current_s3_objects.number_duplicate_events,
            -- Also need the size from the object table.
            object.size
        from current_s3_objects
        join object on object.object_id = current_s3_objects.object_id;
    end;
$$ language plpgsql;