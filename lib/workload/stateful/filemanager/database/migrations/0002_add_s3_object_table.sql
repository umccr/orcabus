create type storage_class as enum ('DeepArchive', 'Glacier', 'GlacierIr', 'IntelligentTiering', 'OnezoneIa', 'Outposts', 'ReducedRedundancy', 'Snow', 'Standard', 'StandardIa');

-- An object contain in AWS S3, maps as a one-to-one relationship with the object table.
create table s3_object(
    -- The object id.
    object_id uuid references object (object_id) primary key,
    -- The S3 storage class of the object.
    storage_class storage_class not null
);