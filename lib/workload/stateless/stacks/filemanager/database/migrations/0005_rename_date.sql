-- Rename `date` to `event_time` as it is clearer what the meaning is compared to `last_modified_date`.
alter table s3_object rename column date to event_time;
