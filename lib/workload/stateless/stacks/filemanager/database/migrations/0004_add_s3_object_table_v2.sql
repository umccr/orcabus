-- An general object table common across all storage types.
create table object_v2 (
    -- The unique id for this object group.
                        object_id uuid not null primary key,
    -- Attributes for a group of objects.
                        attributes jsonb default null
);

-- The type of event
create type event_type as enum (
    'Created',
    'Deleted',
    'Other'
);

-- An object contain in AWS S3, maps as a one-to-one relationship with the object table.
create table s3_object_v2 (
    -- The s3 object id.
    s3_object_id uuid not null primary key,
    -- This is initially deferred because we want to create an s3_object before an object to check for duplicates/order.
    object_id uuid not null references object_v2 (object_id) deferrable initially deferred,
    -- The public id for this object which can be referred to externally to filemanager. Note, there is no public id
    -- on an `object` because objects can be merged which complicates having a permanent public id.
    public_id uuid not null,

    -- Record whether this is a Created or Deleted event.
    event_type event_type not null,

    -- General fields
    -- The bucket of the object.
    bucket text not null,
    -- The key of the object.
    key text not null,
    -- The version id of the object. A 'null' string is used to indicate no version id. This matches logic in AWS which
    -- also returns 'null' strings. See https://docs.aws.amazon.com/AmazonS3/latest/userguide/versioning-workflows.html
    version_id text not null default 'null',
    -- When this event occurred. For created events, this is the creation date, and for deleted events this is the deletion date.
    date timestamptz default null,
    -- The size of the object.
    size bigint default null,
    -- A base64 encoded SHA256 checksum of the object.
    sha256 text default null,

    -- AWS-specific fields
    -- The AWS last modified value.
    last_modified_date timestamptz default null,
    -- An S3-specific e_tag, if it is present.
    e_tag text default null,
    -- The S3 storage class of the object.
    storage_class storage_class default null,
    -- The sequencer value showing ordering between created and deleted events. Used to synchronise out of order and duplicate events.
    sequencer text default null,
    -- Record the number of duplicate events received for this object, useful for debugging.
    number_duplicate_events bigint not null default 0,

    -- Attributes on a single s3_object.
    attributes jsonb default null,

    is_delete_marker boolean not null default false,

    -- The sequencers should be unique with the bucket, key, and its version, otherwise this is a duplicate event.
    constraint sequencer_unique unique (bucket, key, version_id, sequencer)
);
