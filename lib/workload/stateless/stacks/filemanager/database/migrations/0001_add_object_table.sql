-- An general object table common across all storage types.
create table object (
    -- The unique id for this object group.
    object_id uuid not null primary key,
    -- Attributes for a group of objects.
    attributes jsonb default null
    -- The unique id for this object group.
    object_id uuid not null primary key,
    -- Attributes for a group of objects.
    attributes jsonb default null
);
