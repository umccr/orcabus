-- Remove object table because it is no longer used or necessary.
alter table s3_object drop column object_id;
drop table object;

-- Also remove public_id because s3_object_id is okay for now.
alter table s3_object drop column public_id;
