from enum import Enum
from typing import TypedDict, Optional, Annotated
from decimal import Decimal

from pydantic import PlainSerializer


# Miscellanous Enums

class CompressionFormat(Enum):
    ORA = 'ORA'
    GZIP = 'GZIP'


class BoolQueryEnum(Enum):
    TRUE = 'true'
    FALSE = 'false'
    ALL = 'ALL'


CWLFile = TypedDict('CWLFile', {
    'class': str,
    'location': str
})


class CWLDict(TypedDict):
    # Typed Dicts are minimal versions of pydantic BaseModels
    # Don't need to work on snake case vs camel case conversions
    # As CWLDict is merely used to type hint a controlled output
    rgid: str
    rglb: str
    rgsm: str
    lane: int

    read_1: CWLFile
    read_2: Optional[CWLFile]


class PresignedUrl(TypedDict):
    s3Uri: str
    presignedUrl: str
    expiresAt: str


class PresignedUrlModel(TypedDict):
    r1: PresignedUrl
    r2: Optional[PresignedUrl]


FloatDecimal = Annotated[
    Decimal,
    PlainSerializer(lambda x: float(x), return_type=float, when_used='json')
]