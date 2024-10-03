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
    -- If using 'paired' mode, 'Other' will be the event type.
    'Other'
);

-- An object contain in AWS S3, maps as a one-to-one relationship with the object table.
create table s3_object (
    -- The s3 object id.
    s3_object_id uuid not null primary key,

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
    -- When this object was created/deleted.
    event_time timestamptz default null,
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
    constraint sequencer_unique unique (bucket, key, version_id, event_type, sequencer),

    -- The following columns are only used for `paired` mode ingestion.
    -- When this object was deleted, a null value means that the object has not yet been deleted.
    deleted_date timestamptz default null,
    -- A sequencer value for when the object was deleted. Used to synchronise out of order and duplicate events.
    deleted_sequencer text default null,
    -- Record the number of times this event has been considered out of order, useful for debugging.
    number_reordered bigint not null default 0,
    constraint deleted_sequencer_unique unique (bucket, key, version_id, event_type, deleted_sequencer)
);

-- Create an index for ordering `s3_object`s in ascending order.
create index sequencer_index on s3_object (sequencer);
-- A gin index on attributes supported the `@?` operator and jsonpath queries.
create index attributes_index on s3_object using gin (attributes jsonb_path_ops);
-- An index on keys helps querying by prefix.
create index key_index on s3_object (key text_pattern_ops);
