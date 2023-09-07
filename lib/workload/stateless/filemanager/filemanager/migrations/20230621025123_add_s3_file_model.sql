-- As seen in data_portal
create table s3 (
    id bigint not null auto_increment primary key,
    bucket varchar(255) not null,
    `key` varchar(1024) not null,
    size int not null,
    e_tag varchar(255) not null,
    last_modified_date datetime default null,
    storage_class enum('DeepArchive', 'Glacier', 'GlacierIr', 'IntelligentTiering', 'OnezoneIa', 'Outposts', 'ReducedRedundancy', 'Snow', 'Standard', 'StandardIa') default null
);
