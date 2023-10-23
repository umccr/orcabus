-- An general object table common across all storage types.
create table object (
    -- The unique id for this object.
    object_id uuid not null default gen_random_uuid() primary key,
    -- The bucket location.
    bucket varchar(255) not null,
    -- The name of the object.
    key varchar(1024) not null,
    -- The size of the object.
    size int not null,
    -- A unique identifier for the object, if it is present.
    hash varchar(255) default null,
    -- When this object was created.
    created_date timestamptz not null,
    -- When this object was last modified.
    last_modified_date timestamptz not null,
    -- When this object was deleted, a null value means that the object has not yet been deleted.
    deleted_date timestamptz default null,
    -- The date of the object and its id combined.
    portal_run_id varchar(255) not null,
    -- provenance - history of all objects and how they move?
);