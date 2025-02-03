-- Add a reason column that indicates why a new row was added, such as lifecycle
-- transitions or storage class changes.

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
    -- An unknown reason used for old or manual record creation.
    'Unknown'
);

alter table s3_object add column reason reason not null default 'Unknown';
