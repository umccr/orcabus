-- Resets the `is_current_state` to false for a set of objects based on the `bucket`, `key`, `version_id`
-- and `sequencer`. This is used to update the current state so that a new object can have it's `is_current_state`
-- set to true based on whether it is a `Created` or `Deleted` event.

-- Unnest input.
with input as (
    select
        *
    from unnest(
        $1::text[],
        $2::text[],
        $3::text[],
        $4::text[]
    ) as input (
        bucket,
        key,
        version_id,
        sequencer
    )
),
-- Select objects to update.
to_update as (
    select * from input cross join lateral (
        select
            s3_object_id,
            -- This finds the first value in the set which represents the most up-to-date state.
            -- If ordered by the sequencer, the first row is the one that needs to have `is_current_state`
            -- set to 'true' only for `Created` events, as `Deleted` events are always non-current state.
            case when row_number() over (order by s3_object.sequencer desc nulls last) = 1 then
                event_type = 'Created'
            -- Set `is_current_state` to 'false' for all other rows, as this is now historical data.
            else
                false
            end as updated_state
        from s3_object
        where
            -- This should be fairly efficient as it's only targeting objects where `is_current_state` is true,
            -- or objects with the highest sequencer values (in case of an out-of-order event). This means that
            -- although there is a performance impact for running this on ingestion, it should be minimal with
            -- the right indexes.
            input.bucket = s3_object.bucket and
            input.key = s3_object.key and
            -- Note that we need to fetch all versions of an object, because when a record is updated,
            -- previous versions need to have their `is_current_state` set to false.
            -- This is an optimization which prevents querying against all objects in the set.
            (
                -- Only need to update current objects
                s3_object.is_current_state = true or
                -- Or objects where there is a newer sequencer than the one being processed.
                -- This is required in case an out-of-order event is encountered. This always
                -- includes the object being processed as it's required for the above row-logic.
                s3_object.sequencer >= input.sequencer
            )
    ) s3_object
)
update s3_object
set is_current_state = updated_state
from to_update
where s3_object.s3_object_id = to_update.s3_object_id
returning s3_object.s3_object_id, s3_object.is_current_state;
