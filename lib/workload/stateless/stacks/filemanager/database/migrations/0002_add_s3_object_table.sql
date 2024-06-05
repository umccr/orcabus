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

-- The type of event for this s3_object record.
create type event_type as enum (
    'Created',
    'Deleted',
    'Other'
);

-- An object contain in AWS S3, maps as a one-to-one relationship with the object table.
create table s3_object (
    -- The s3 object id.
    s3_object_id uuid not null primary key,
    -- This is initially deferred because we want to create an s3_object before an object to check for duplicates/order.
    object_id uuid not null references object (object_id) deferrable initially deferred,
    -- The public id for this object which can be referred to externally to filemanager. Note, there is no public id
    -- on an `object` because objects can be merged which complicates having a permanent public id.
    public_id uuid not null,

    -- General fields
    -- The kind of event of this s3_object.
    event_type event_type not null,
    -- The bucket of the object.
    bucket text not null,
    -- The key of the object.
    key text not null,
    -- The version id of the object. A 'null' string is used to indicate no version id. This matches logic in AWS which
    -- also returns 'null' strings. See https://docs.aws.amazon.com/AmazonS3/latest/userguide/versioning-workflows.html
    version_id text not null default 'null',
    -- When this object was created/deleted. For created objects, this is the date the object was created. For deleted
    -- objects, this is the date the object was deleted.
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
    -- A sequencer value for when the object. Used to synchronise out of order and duplicate events.
    sequencer text default null,
    -- A delete marker is a special object that is created when a versioned object is deleted.
    is_delete_marker boolean not null default false,
    -- Record the number of duplicate events received for this object, useful for debugging.
    number_duplicate_events bigint not null default 0,

    -- Attributes on a single s3_object.
    attributes jsonb default null,

    -- The sequencers should be unique with the bucket, key, version_id and event_type,
    -- otherwise this is a duplicate event.
    constraint sequencer_unique unique (bucket, key, version_id, event_type, sequencer)
);
