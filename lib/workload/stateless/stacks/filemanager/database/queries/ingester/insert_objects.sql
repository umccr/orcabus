-- Bulk insert of objects
insert into object (object_id)
values (
    unnest($1::uuid[])
);
