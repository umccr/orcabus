-- The AWS S3 storage classes.
create type storage_class as enum (
    'DeepArchive',
    'Glacier',
    'GlacierIr',
    'IntelligentTiering',
    'OnezoneIa',
    'Outposts',
    'ReducedRedundancy',
    'Snow',
    'Standard',
    'StandardIa'
);

-- An object contain in AWS S3, maps as a one-to-one relationship with the object table.
create table s3_object (
    -- The s3 object id.
    s3_object_id uuid not null primary key,
    -- This is initially deferred because we want to create an s3_object before an object to check for duplicates/order.
    object_id uuid not null references object (object_id) deferrable initially deferred,

    -- General fields
    -- The bucket of the object.
    bucket text not null,
    -- The key of the object.
    key text not null,
    -- The version id of the object. A 'null' string is used to indicate no version id. This matches logic in AWS which
    -- also returns 'null' strings. See https://docs.aws.amazon.com/AmazonS3/latest/userguide/versioning-workflows.html
    version_id text not null default 'null',
    -- When this object was created. A null value here means that a deleted event has occurred before a created event.
    created_date timestamptz default null,
    -- When this object was deleted, a null value means that the object has not yet been deleted.
    deleted_date timestamptz default null,
    -- provenance - history of all objects and how they move?
    -- The size of the object.
    size integer default null,
    -- A unique identifier for the object, if it is present.
    checksum text default null,

    -- AWS-specific fields
    -- The AWS last modified value.
    last_modified_date timestamptz default null,
    -- An S3-specific e_tag, if it is present.
    e_tag text default null,
    -- The S3 storage class of the object.
    storage_class storage_class default null,
    -- A sequencer value for when the object was created. Used to synchronise out of order and duplicate events.
    created_sequencer text default null,
    -- A sequencer value for when the object was deleted. Used to synchronise out of order and duplicate events.
    deleted_sequencer text default null,
    -- Record the number of times this event has been considered out of order, useful for debugging.
    number_reordered integer not null default 0,
    -- Record the number of duplicate events received for this object, useful for debugging.
    number_duplicate_events integer not null default 0,

    -- The sequencers should be unique with the bucket, key, and its version, otherwise this is a duplicate event.
    constraint created_sequencer_unique unique (bucket, key, version_id, created_sequencer),
    constraint deleted_sequencer_unique unique (bucket, key, version_id, deleted_sequencer)
);
