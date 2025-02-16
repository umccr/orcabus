#!/usr/bin/env python

S3_INGEST_ID_URI_MAP_CACHE = {}


def update_cache(s3_ingest_id: str, uri: str):
    global S3_INGEST_ID_URI_MAP_CACHE
    S3_INGEST_ID_URI_MAP_CACHE[s3_ingest_id] = uri