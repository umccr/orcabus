-- Create an index for ordering `s3_object`s in ascending order.
-- TODO this should be created `concurrently` when running migrations without transactions is released:
-- https://github.com/launchbadge/sqlx/issues/767
create index sequencer_index on s3_object (sequencer);
