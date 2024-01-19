-- Bulk insert of s3 objects.
insert into s3_object (object_id, bucket, key, e_tag, storage_class, created_sequencer)
values (
    unnest($1::uuid[]),
    unnest($2::text[]),
    unnest($3::text[]),
    unnest($4::text[]),
    unnest($5::storage_class[]),
    unnest($6::text[])
) on conflict on constraint created_sequencer_unique do update
    set number_duplicate_events = s3_object.number_duplicate_events + 1;