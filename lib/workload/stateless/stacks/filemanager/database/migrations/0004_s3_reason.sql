-- Add a reason column that indicates why a new row was added, such as lifecycle
-- transitions or storage class changes. Also adds archive type for intelligent tiering.

-- The reason for the s3 object row.
create type reason as enum (
    -- The object was created using `PutObject`.
    'CreatedPut',
    -- The object was created using `PostObject`.
    'CreatedPost',
    -- The object was created using `CopyObject`.
    'CreatedCopy',
    -- The object was created using multipart uploads.
    'CreatedCompleteMultipartUpload',
    -- The object was deleted using APIs like `DeleteObject`.
    'Deleted',
    -- The object was deleted using lifecycle expiration rules.
    'DeletedLifecycle',
    -- The object was restored from archive.
    'Restored',
    -- The object's restored copy was expired.
    'RestoreExpired',
    -- The object's storage class was changed, including changes intelligent tiering classes.
    'StorageClassChanged',
    -- This event was generated from a crawl operation like S3 inventory.
    'Crawl',
    -- An unknown reason used for old or manual record creation.
    'Unknown'
);

-- The intelligent tiering archive status.
create type archive_status as enum (
    -- The object is in the archive access tier.
    'ArchiveAccess',
    -- The object is in the deep archive access tier.
    'DeepArchiveAccess'
);

-- Add the reason column defaulting to an unknown value.
alter table s3_object add column reason reason not null default 'Unknown';
-- Add the archive status column. This can only have a value if the storage class is also `IntelligentTiering`.
alter table s3_object add column archive_status archive_status default null;
-- Convenience column for determining whether an object is immediately accessible.
alter table s3_object add column is_accessible bool not null generated always as (
    is_current_state and
    storage_class is not null and
    storage_class != 'Glacier' and
    (storage_class != 'DeepArchive' or reason = 'Restored') and
    (storage_class != 'IntelligentTiering' or archive_status is null)
) stored;
