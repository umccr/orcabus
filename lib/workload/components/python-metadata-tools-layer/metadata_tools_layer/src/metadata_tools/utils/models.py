#!/usr/bin/env python3

from typing import (
    TypedDict,
    Optional, List
)


# Base Objects
class MetadataBase(TypedDict):
    orcabusId: str


class LibraryBase(MetadataBase):
    libraryId: str


class SampleBase(MetadataBase):
    sampleId: str


class SubjectBase(MetadataBase):
    subjectId: str


class IndividualBase(MetadataBase):
    individualId: str


class ProjectBase(MetadataBase):
    projectId: str


class ContactBase(MetadataBase):
    contactId: str


# Detailed Objects - Often outputs of API calls from other metadata endpoints
class LibraryDetail(LibraryBase):
    phenotype: Optional[str]
    workflow: Optional[str]
    quality: Optional[str]
    type: Optional[str]
    assay: Optional[str]
    coverage: Optional[float]
    overrideCycles: Optional[str]


class SampleDetail(SampleBase):
    externalSampleId: Optional[str]
    source: Optional[str]


class SubjectDetail(SubjectBase):
    pass


class IndividualDetail(IndividualBase):
    source: Optional[str]


class ProjectDetail(ProjectBase):
    name: Optional[str]
    description: Optional[str]


class ContactDetail(ContactBase):
    name: Optional[str]
    email: Optional[str]
    description: Optional[str]


# Add complete objects
# These contain the sets of other metadata objects
class Library(LibraryDetail):
    sample: Optional[SampleDetail]
    subject: Optional[SubjectDetail]
    projectSet: Optional[List[ProjectDetail]]


class Sample(SampleDetail):
    librarySet: Optional[List[LibraryDetail]]


class Subject(SubjectDetail):
    librarySet: Optional[List[LibraryDetail]]
    individualSet: Optional[List[IndividualDetail]]


class Individual(IndividualDetail):
    subjectSet: Optional[List[SubjectDetail]]


class Project(ProjectDetail):
    contactSet: Optional[List[ContactDetail]]


class Contact(ContactDetail):
    projectSet: Optional[List[ProjectDetail]]
