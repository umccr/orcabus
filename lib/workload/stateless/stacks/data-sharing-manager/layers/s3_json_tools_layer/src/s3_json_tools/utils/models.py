#!/usr/bin/env python3

"""
This file contains the models for the database.
"""

import typing
from typing import Union
from pathlib import Path

if typing.TYPE_CHECKING:
    from filemanager_tools import FileObject
    from metadata_tools import Library
    from workflow_tools import WorkflowRun

class FileObjectWithPresignedUrlTypeDef(FileObject):
    presignedUrl: str


class FileObjectWithMetadataTypeDef(FileObject):
    """
    A file object with metadata.
    """
    library: Library
    workflowRun: WorkflowRun
    relativePath: Union[Path, str]


class FileObjectWithMetadataAndPresignedUrlTypeDef(
    FileObjectWithMetadataTypeDef,
    FileObjectWithPresignedUrlTypeDef,
):
    pass