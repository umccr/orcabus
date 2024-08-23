-- A gin index on attributes supported the `@?` operator and jsonpath queries.
create index attributes_index on s3_object using gin (attributes jsonb_path_ops);
-- An index on keys helps querying by prefix.
create index key_index on s3_object (key text_pattern_ops);
