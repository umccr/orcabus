-- Bulk insert of s3 objects.
insert into s3_object (
    s3_object_id,
    object_id,
    bucket,
    key,
    -- We default the created date to a value event if this is a deleted event,
    -- as we are expecting this to get updated.
    created_date,
    deleted_date,
    last_modified_date,
    e_tag,
    storage_class,
    version_id,
    deleted_sequencer,
    maximum_sequencer
)
values (
   unnest($1::uuid[]),
   unnest($2::uuid[]),
   unnest($3::text[]),
   unnest($4::text[]),
   unnest($5::timestamptz[]),
   unnest($6::timestamptz[]),
   unnest($7::timestamptz[]),
   unnest($8::text[]),
   unnest($9::storage_class[]),
   unnest($10::text[]),
   unnest($11::text[]),
   unnest($12::text[])
) on conflict on constraint deleted_sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1
    returning object_id, number_duplicate_events;
