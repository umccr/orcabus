-- As seen in data_portal
create table s3 (
    id bigint not null auto_increment,
    bucket varchar not null,
    key longtext not null,
    size bigint not null,
    last_modified_date datetime not null,
    e_tag varchar not null,
    unique_hash varchar not null,
);