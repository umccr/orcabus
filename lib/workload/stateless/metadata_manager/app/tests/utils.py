from app.models import Individual, Subject, Specimen, Library
from app.tests.factories import LibraryFactory, SubjectFactory, SpecimenFactory, IndividualFactory


def clear_all_data():
    """This function clear all existing models objcet"""
    Library.objects.all().delete()
    Specimen.objects.all().delete()
    Subject.objects.all().delete()
    Individual.objects.all().delete()


def insert_mock_1():
    """
    This function is a shortcut to clear and insert a set of mock data
    """
    clear_all_data()

    library = LibraryFactory()
    specimen = SpecimenFactory()
    subject = SubjectFactory()
    individual = IndividualFactory()

    # Linking
    library.specimen = specimen
    library.save()

    specimen.subjects.add(subject)
    specimen.save()

    subject.individual = individual
    subject.save()
