-- Select the current maximum sequencer values for a given set of buckets, keys, and version_ids.
-- select array(
--    select maximum_sequencer
--    from s3_object
--    where s3_object.bucket = bucket and s3_object.key = key and s3_object.version_id = version_id
--    limit 1
-- ) from unnest($1::text[], $2::text[], $3::text[]) as data(bucket, key, version_id);

-- Select the matching s3_object which should be re-ordered based on the deleted event. Returns nothing
-- if there is no matching event.
select object_id from s3_object
where
    s3_object.bucket = $1::text and
    s3_object.key = $2::text and
    s3_object.version_id = $3::text and
    s3_object.created_sequencer < $4::text and
    (
        s3_object.deleted_sequencer is null or
        s3_object.deleted_sequencer > $4::text
    );