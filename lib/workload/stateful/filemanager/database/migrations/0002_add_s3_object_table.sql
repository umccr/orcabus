create type storage_class as enum ('DeepArchive', 'Glacier', 'GlacierIr', 'IntelligentTiering', 'OnezoneIa', 'Outposts', 'ReducedRedundancy', 'Snow', 'Standard', 'StandardIa');

-- An object contain in AWS S3, maps as a one-to-one relationship with the object table.
create table s3_object(
    -- The object id.
    object_id uuid references object (object_id) primary key,
    -- Duplicate the bucket here because it is useful for conflicts. This must match the bucket in object.
    bucket text references object(bucket) not null,
    -- Duplicate the key here because it is useful for conflicts. This must match the key in object.
    key text references object(bucket) not null,
    -- An S3-specific e_tag, if it is present.
    e_tag text default null,
    -- The S3 storage class of the object.
    storage_class storage_class not null,
    -- A sequencer value for when the object was created. Used to synchronise out of order and duplicate events.
    created_sequencer text default null,
    -- A sequencer value for when the object was deleted. Used to synchronise out of order and duplicate events.
    deleted_sequencer text default null,
    -- Record whether the event that generated this object was ever out of order, useful for debugging.
    event_out_of_order boolean not null default false,
    -- Record the number of duplicate events received for this object, useful for debugging.
    number_duplicate_events integer not null default 0
);