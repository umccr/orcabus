-- A object group used to store attributes on groups of objects.
create table object_group (
    -- The unique id for this object group.
    object_group_id uuid not null primary key,
    -- An optional group name used to identify the grouping.
    group_name text default null,
    -- Identifies whether this group represents objects that are the same.
    -- Can be set internally by filemanager for objects with the same checksum.
    is_same_object bool default null,
    -- Attributes for a group of objects.
    attributes jsonb default null
);
