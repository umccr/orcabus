-- An general object table common across all storage types.
create table object (
    -- The unique id for this object.
    object_id uuid not null primary key
);
