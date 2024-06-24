alter table object rename to object_group;
alter table object_group rename object_id to object_group_id;
alter table s3_object rename object_id to object_group_id;
