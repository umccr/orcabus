-- Resets the `is_current_state` to false for a set of objects based on the `bucket`, `key`, `version_id`
-- and `sequencer`. This is used to reset the current state so that a new object can have it's `is_current_state`
-- set to true.

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
    select s3_object_id from input cross join lateral (
        select
            s3_object_id
        from s3_object
        where
            input.bucket = s3_object.bucket and
            input.key = s3_object.key and
            input.version_id = s3_object.version_id and
            -- Only the objects older than the input.
            input.sequencer >= s3_object.sequencer and
            -- Only need to update current objects.
            s3_object.is_current_state = true
        for update
    ) s3_object
)
update s3_object
set is_current_state = false
from to_update
where s3_object.s3_object_id = to_update.s3_object_id;
