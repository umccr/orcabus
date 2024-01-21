-- An general object table common across all storage types.
create table object (
    -- The unique id for this object.
    object_id uuid not null default gen_random_uuid() primary key,
    -- The size of the object.
    size integer default null,
    -- A unique identifier for the object, if it is present.
    checksum text default null
);
