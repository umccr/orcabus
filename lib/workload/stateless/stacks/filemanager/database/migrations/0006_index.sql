-- A gin index on attributes supported the `@?` operator and jsonpath queries.
create index attributes_index on s3_object using gin (attributes jsonb_path_ops);
