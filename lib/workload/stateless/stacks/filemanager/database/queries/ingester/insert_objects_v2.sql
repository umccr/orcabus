-- Bulk insert of objects
insert into object_v2 (object_id)
values (
    unnest($1::uuid[])
);
