-- Bulk insert of s3 objects.
insert into s3_object (
    s3_object_id,
    object_id,
    bucket,
    key,
    created_date,
    last_modified_date,
    e_tag,
    storage_class,
    version_id,
    created_sequencer,
    maximum_sequencer
)
values (
    unnest($1::uuid[]),
    unnest($2::uuid[]),
    unnest($3::text[]),
    unnest($4::text[]),
    unnest($5::timestamptz[]),
    unnest($6::timestamptz[]),
    unnest($7::text[]),
    unnest($8::storage_class[]),
    unnest($9::text[]),
    unnest($10::text[]),
    unnest($11::text[])
) on conflict on constraint created_sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1
    returning object_id, number_duplicate_events;
