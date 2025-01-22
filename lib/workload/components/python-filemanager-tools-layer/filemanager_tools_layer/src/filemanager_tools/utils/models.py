from pydantic import BaseModel

from typing import Optional

"""
Example File Object response
    {
      "attributes": null,
      "bucket": "string",
      "deletedDate": "2025-01-19T23:32:42.747Z",
      "deletedSequencer": "string",
      "eTag": "string",
      "eventTime": "2025-01-19T23:32:42.747Z",
      "eventType": "Created",
      "ingestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "isCurrentState": true,
      "isDeleteMarker": true,
      "key": "string",
      "lastModifiedDate": "2025-01-19T23:32:42.747Z",
      "numberDuplicateEvents": 9007199254740991,
      "numberReordered": 9007199254740991,
      "s3ObjectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "sequencer": "string",
      "sha256": "string",
      "size": 9007199254740991,
      "storageClass": null,
      "versionId": "string"
    }
"""


class FileObject(BaseModel):
    # Identifier
    s3ObjectId: str

    # Path attributes
    bucket: str
    key: str

    # File attributes
    eTag: str
    eventTime: str
    eventType: str
    ingestId: str
    isCurrentState: bool
    isDeleteMarker: bool
    lastModifiedDate: str
    numberDuplicateEvents: int
    numberReordered: int
    sequencer: str
    size: int
    storageClass: str

    # Optional attributes
    deletedDate: Optional[str] = None
    deletedSequencer: Optional[str] = None
    versionId: Optional[str] = None
    sha256: Optional[str] = None