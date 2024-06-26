-- Bulk insert of s3 objects.
insert into s3_object (
    s3_object_id,
    public_id,
    bucket,
    key,
    date,
    size,
    sha256,
    last_modified_date,
    e_tag,
    storage_class,
    version_id,
    sequencer,
    is_delete_marker,
    event_type
)
values (
    unnest($1::uuid[]),
    unnest($2::uuid[]),
    unnest($3::text[]),
    unnest($4::text[]),
    unnest($5::timestamptz[]),
    unnest($6::bigint[]),
    unnest($7::text[]),
    unnest($8::timestamptz[]),
    unnest($9::text[]),
    unnest($10::storage_class[]),
    unnest($11::text[]),
    unnest($12::text[]),
    unnest($13::boolean[]),
    unnest($14::event_type[])
) on conflict on constraint sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1
    returning number_duplicate_events;
