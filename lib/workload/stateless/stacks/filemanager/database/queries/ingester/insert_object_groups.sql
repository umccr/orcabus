-- Bulk insert of objects
insert into object_group (object_id)
values (
    unnest($1::uuid[])
);
