import factory

from app.models import Subject, Specimen, Library

INDIVIDUAL_1 = {
    "individual_id": "I001"
}

SUBJECT_1 = {
    "lab_subject_id": "SBJ001",
    "external_subject_id": "EXT_SUB_ID_A"
}

SPECIMEN_1 = {
    "lab_specimen_id": "PRJ001",
    "external_specimen_id": "EXT_SPC_ID_A",
    "source": "FFPE"
}

LIBRARY_1 = {
    "library_id": "LIB01",
    "phenotype": "negative-control",
    "workflow": "clinical",
    "quality": "good",
    "type": "WTS",
    "assay": "NebRNA",
    "coverage": 6.0,
    'project_owner': 'test_owner',
    'project_name': 'test_project'
}


class SubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subject

    lab_subject_id = SUBJECT_1['lab_subject_id']
    external_subject_id = SUBJECT_1['external_subject_id']


class SpecimenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Specimen

    lab_specimen_id = SPECIMEN_1['lab_specimen_id']
    external_specimen_id = SPECIMEN_1['external_specimen_id']
    source = SPECIMEN_1['source']


class LibraryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Library

    library_id = LIBRARY_1["library_id"]
    phenotype = LIBRARY_1["phenotype"]
    workflow = LIBRARY_1["workflow"]
    quality = LIBRARY_1["quality"]
    type = LIBRARY_1["type"]
    assay = LIBRARY_1["assay"]
    coverage = LIBRARY_1["coverage"]
