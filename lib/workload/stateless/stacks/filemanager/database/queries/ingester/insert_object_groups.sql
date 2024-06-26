-- Bulk insert of objects
insert into object_group (object_group_id)
values (
    unnest($1::uuid[])
);
