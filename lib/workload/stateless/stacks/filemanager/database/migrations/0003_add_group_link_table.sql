-- A link between object_groups and s3_objects, used to allow arbirary groupings of s3_objects.
create table group_link (
    -- The unique id for this group link.
    group_link_id uuid not null primary key,
    -- This is initially deferred because we want to create an s3_object before an object to check for duplicates/order.
    object_group_id uuid not null references object_group (object_group_id),
    -- This is initially deferred because we want to create an s3_object before an object to check for duplicates/order.
    s3_object_id uuid not null references s3_object (s3_object_id)
);
