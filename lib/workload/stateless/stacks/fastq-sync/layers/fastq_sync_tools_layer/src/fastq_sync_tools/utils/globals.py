#!/usr/bin/env python

from enum import Enum

ACTIVE_STORAGE_CLASSES = [
    "Standard",
    "StandardIa",
    "IntelligentTiering",
    "GlacierIr",
    "Glacier",
    "DeepArchive",
]

BYOB_BUCKET_PREFIX_ENV_VAR = "BYOB_BUCKET_PREFIX"


class Requirements(Enum):
  HAS_ACTIVE_READ_SET = "hasActiveReadSet"
  HAS_QC = "hasQc"
  HAS_FINGERPRINT = "hasFingerprint"
  HAS_FILE_COMPRESSION_INFORMATION = "hasFileCompressionInformation"

