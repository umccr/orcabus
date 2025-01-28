# Standard imports
from pydantic import BaseModel
from typing import Self, Optional

# Model imports
from .file_storage import (
    FileStorageObjectData, FileStorageObjectResponse, FileStorageObjectCreate
)


# Base class
class FastqPairStorageObjectBase(BaseModel):
    r1: FileStorageObjectData
    r2: Optional[FileStorageObjectData] = None


# Response class
class FastqPairStorageObjectResponse(FastqPairStorageObjectBase):
    r1: FileStorageObjectResponse
    r2: Optional[FileStorageObjectResponse] = None

    def model_dump(self, **kwargs) -> Self:
        # Complete recursive serialization manually
        data = super().model_dump(**kwargs)

        # Serialize r1 and r2
        data['r1'] = self.r1.model_dump(by_alias=True)
        if self.r2:
            data['r2'] = self.r2.model_dump(by_alias=True)
        return data

class FastqPairStorageObjectCreate(FastqPairStorageObjectBase):
    r1: FileStorageObjectCreate
    r2: Optional[FileStorageObjectCreate] = None

    def model_dump(self, **kwargs) -> 'FastqPairStorageObjectResponse':
        return (
            FastqPairStorageObjectResponse(**super().model_dump()).
            model_dump()
        )


class FastqPairStorageObjectUpdate(FastqPairStorageObjectCreate):
    pass


class FastqPairStorageObjectData(FastqPairStorageObjectBase):
    def to_dict(self) -> 'FastqPairStorageObjectResponse':
        return FastqPairStorageObjectResponse(**self.model_dump()).model_dump()