-- Bulk insert of s3 objects.
insert into s3_object (object_id, storage_class)
values (unnest(?), unnest(?));