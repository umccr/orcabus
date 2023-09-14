-- Bulk insert of objects
insert into object (object_id, bucket, key, size, hash, created_date, last_modified_date, portal_run_id)
values (
    unnest($1::uuid[]),
    unnest($2::varchar[]),
    unnest($3::varchar[]),
    unnest($4::int[]),
    unnest($5::varchar[]),
    unnest($6::timestamptz[]),
    unnest($7::timestamptz[]),
    unnest($8::varchar[])
);