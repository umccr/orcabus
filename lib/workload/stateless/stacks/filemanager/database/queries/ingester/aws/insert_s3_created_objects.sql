-- Bulk insert of s3 objects.
insert into s3_object (
    s3_object_id,
    bucket,
    key,
    event_time,
    size,
    sha256,
    last_modified_date,
    e_tag,
    storage_class,
    version_id,
    sequencer,
    is_delete_marker,
    reason,
    event_type,
    ingest_id,
    attributes
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
    unnest($12::boolean[]),
    unnest($13::reason[]),
    unnest($14::event_type[]),
    unnest($15::uuid[]),
    unnest($16::jsonb[])
) on conflict on constraint sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1
    returning s3_object_id, number_duplicate_events;
