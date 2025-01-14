import factory

from app.models import Subject, Sample, Library, Project, Contact, Individual

INDIVIDUAL_1 = {
    "individual_id": "SBJ001",
    "source": "lab"
}

SUBJECT_1 = {
    "subject_id": "XS-0001",
}

SAMPLE_1 = {
    "sample_id": "PRJ001",
    "external_sample_id": "EXT_SPM_ID_A",
    "source": "FFPE"
}

LIBRARY_1 = {
    "library_id": "LIB01",
    "phenotype": "negative-control",
    "workflow": "clinical",
    "quality": "good",
    "type": "WTS",
    "assay": "NebRNA",
    "override_cycles": "Y151;I8N2;I8N2;Y151",
    "coverage": 6.0,
    'project_owner': 'test_owner',
    'project_name': 'test_project'
}

PROJECT_1 = {
    'project_id': 'prj-01',
    'name': 'test_project'
}

CONTACT_1 = {
    'contact_id': 'doe-01',
    'name': 'doe',
}


class IndividualFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Individual

    individual_id = INDIVIDUAL_1['individual_id']
    source = INDIVIDUAL_1['source']


class SubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subject

    subject_id = SUBJECT_1['subject_id']


class SampleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sample

    sample_id = SAMPLE_1['sample_id']
    external_sample_id = SAMPLE_1['external_sample_id']
    source = SAMPLE_1['source']


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
    override_cycles = LIBRARY_1["override_cycles"]

class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    project_id = PROJECT_1['project_id']
    name = PROJECT_1['name']


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    contact_id = CONTACT_1['contact_id']
    name = CONTACT_1['name']
