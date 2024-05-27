-- A delete marker is a special object that is created when a versioned object is deleted.
alter table s3_object add column is_delete_marker boolean not null default false;
