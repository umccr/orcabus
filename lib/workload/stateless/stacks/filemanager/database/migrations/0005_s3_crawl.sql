-- Create a type to track crawl operation status.
create type crawl_status as enum (
    'InProgress',
    'Completed',
    'Failed'
);

-- Add a table to track crawl operations.
create table s3_crawl (
    -- The primary key id.
    s3_crawl_id uuid not null primary key,
    -- The status of this crawl invocation.
    status crawl_status not null default 'InProgress',
    -- When the crawl was started.
    started timestamptz not null default now(),
    -- The bucket to ingest at.
    bucket text not null,
    -- The prefix of objects to ingest.
    prefix text default null,
    -- How long the crawl took. This will only be set when the status is 'Completed'.
    execution_time_seconds int default null,
    -- The number of objects that were ingested. This will only be set when the status is 'Completed'.
    n_objects bigint default null
);

-- There should only ever be one `InProgress` crawl at a time for a bucket. This enforces that on a database-level.
create unique index s3_crawl_unique_in_progress on s3_crawl (bucket) where status = 'InProgress';