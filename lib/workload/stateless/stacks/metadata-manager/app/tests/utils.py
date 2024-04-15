from app.models import Subject, Specimen, Library
from app.tests.factories import LibraryFactory, SubjectFactory, SpecimenFactory


def clear_all_data():
    """This function clear all existing models objcet"""
    Library.objects.all().delete()
    Specimen.objects.all().delete()
    Subject.objects.all().delete()


def insert_mock_1():
    """
    This function is a shortcut to clear and insert a set of mock data
    """
    clear_all_data()

    library = LibraryFactory()
    specimen = SpecimenFactory()
    subject = SubjectFactory()

    # Linking
    library.specimen = specimen
    library.save()

    specimen.subjects.add(subject)
    specimen.save()
