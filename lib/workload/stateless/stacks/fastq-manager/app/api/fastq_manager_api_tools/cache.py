#!/usr/bin/env python

import typing
from typing import Dict

if typing.TYPE_CHECKING:
    from filemanager_tools import FileObject

S3_INGEST_ID_TO_OBJ_MAP_CACHE: Dict[str, 'FileObject'] = {}


def update_cache(ingest_id: str, s3_obj: 'FileObject'):
    global S3_INGEST_ID_TO_OBJ_MAP_CACHE
    S3_INGEST_ID_TO_OBJ_MAP_CACHE[ingest_id] = s3_obj