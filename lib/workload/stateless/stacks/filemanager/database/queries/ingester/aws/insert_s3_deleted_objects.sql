-- Bulk insert of s3 objects.
insert into s3_object (
    s3_object_id,
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
    reason,
    archive_status,
    event_type
)
values (
    unnest($1::uuid[]),
    unnest($2::text[]),
    unnest($3::text[]),
    unnest($4::timestamptz[]),
    unnest($5::bigint[]),
    unnest($6::text[]),
    unnest($7::timestamptz[]),
    unnest($8::text[]),
    unnest($9::storage_class[]),
    unnest($10::text[]),
    unnest($11::text[]),
    unnest($12::bigint[]),
    unnest($13::boolean[]),
    unnest($14::reason[]),
    unnest($15::archive_status[]),
    unnest($16::event_type[])
) on conflict on constraint deleted_sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1
    returning s3_object_id, number_duplicate_events;
