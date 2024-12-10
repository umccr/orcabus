from django.core.exceptions import ObjectDoesNotExist

from app.models import Subject, Sample, Library, Project, Contact, Individual
from app.tests.factories import LibraryFactory, IndividualFactory, SubjectFactory, SampleFactory, \
    ProjectFactory, ContactFactory


def clear_all_data():
    """This function clear all existing models object"""
    Library.objects.all().delete()
    Sample.objects.all().delete()
    Subject.objects.all().delete()
    Project.objects.all().delete()
    Contact.objects.all().delete()
    Individual.objects.all().delete()


def insert_mock_1():
    """
    This function is a shortcut to clear and insert a set of mock data
    """
    clear_all_data()

    library = LibraryFactory()
    sample = SampleFactory()
    subject = SubjectFactory()
    contact = ContactFactory()
    project = ProjectFactory()
    individual = IndividualFactory()

    # Linking
    project.contact_set.add(contact)
    library.sample = sample
    library.subject = subject
    library.save()
    library.project_set.add(project)

    subject.individual_set.add(individual)
    subject.save()


def is_obj_exists(obj, **kwargs):
    try:
        obj.objects.get(**kwargs)
        return True
    except ObjectDoesNotExist:
        return False
