-- Bulk insert of s3 objects.
insert into s3_object (
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
    deleted_sequencer
)
values (
   unnest($1::uuid[]),
   unnest($2::text[]),
   unnest($3::text[]),
   unnest($4::timestamptz[]),
   unnest($5::timestamptz[]),
   unnest($6::timestamptz[]),
   unnest($7::text[]),
   unnest($8::storage_class[]),
   unnest($9::text[])
) on conflict on constraint deleted_sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1;
