-- Bulk insert of s3 objects.
insert into s3_object (
    s3_object_id,
    object_id,
    public_id,
    bucket,
    key,
    deleted_date,
    size,
    sha256,
    last_modified_date,
    e_tag,
    storage_class,
    version_id,
    deleted_sequencer,
    number_reordered,
    is_delete_marker,
    event_type
)
values (
    unnest($1::uuid[]),
    unnest($2::uuid[]),
    unnest($3::uuid[]),
    unnest($4::text[]),
    unnest($5::text[]),
    unnest($6::timestamptz[]),
    unnest($7::bigint[]),
    unnest($8::text[]),
    unnest($9::timestamptz[]),
    unnest($10::text[]),
    unnest($11::storage_class[]),
    unnest($12::text[]),
    unnest($13::text[]),
    unnest($14::bigint[]),
    unnest($15::boolean[]),
    unnest($16::event_type[])
) on conflict on constraint deleted_sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1
    returning object_id, number_duplicate_events;
