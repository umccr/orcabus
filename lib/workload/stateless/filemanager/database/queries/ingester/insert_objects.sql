-- Bulk insert of objects
insert into object (object_id, size, checksum)
values (
    unnest($1::uuid[]),
    unnest($2::int[]),
    unnest($3::text[])
);
