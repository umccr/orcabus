-- Creates the `is_current_state` column to separate objects by current and historical records.

begin;

-- -- Initially, set the `is_current_state` to false to make migrating existing data easier.
alter table s3_object add column is_current_state boolean not null default false;

-- This migrates existing data, first find the current state and update existing records.
with to_update as (
    -- Get all records representing the current state.
    select * from (
        select distinct on (bucket, key) * from s3_object
        order by bucket, key, sequencer desc
    ) as s3_object
    where event_type = 'Created' and is_delete_marker = false
)
-- Update `is_current_state` on existing records.
update s3_object
set is_current_state = true
from to_update
where s3_object.s3_object_id = to_update.s3_object_id;

-- Then, set the default to true to match new logic using `is_current_state`.
alter table s3_object alter column is_current_state set default true;

-- Create an indexes for now, although partitioning will be required later.
create index is_current_state_index on s3_object (is_current_state);
-- This helps the query which resets the current state when ingesting objects.
create index reset_current_state_index on s3_object (bucket, key, sequencer, is_current_state);

commit;
