-- Select all objects that meet regexp criteria
-- FIXME: Should not trust user input, should be a bit more robust than like/similar to
select from s3_object where key like $1;