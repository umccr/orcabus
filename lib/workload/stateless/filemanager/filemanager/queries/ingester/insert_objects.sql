-- Bulk insert of objects
insert into object (object_id, bucket, key, size, e_tag, created_date, last_modified_date, deleted_date, portal_run_id)
values (unnest(?), unnest(?), unnest(?), unnest(?), unnest(?), unnest(?), unnest(?), unnest(?), unnest(?));