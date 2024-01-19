-- Bulk insert of objects
insert into object (object_id, bucket, key, size, checksum, created_date, last_modified_date, portal_run_id)
values (
    unnest($1::uuid[]),
    unnest($2::text[]),
    unnest($3::text[]),
    unnest($4::int[]),
    unnest($5::text[]),
    unnest($6::timestamptz[]),
    unnest($7::timestamptz[]),
    unnest($8::text[])
);