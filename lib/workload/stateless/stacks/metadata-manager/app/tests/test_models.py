import logging

from unittest.mock import  patch

from django.test import TestCase

from app.models import Subject, Sample, Library, Contact, Project, Individual
from .factories import LIBRARY_1, SAMPLE_1, INDIVIDUAL_1, SUBJECT_1, PROJECT_1, CONTACT_1
from .utils import insert_mock_1

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ModelTestCase(TestCase):
    def setUp(self):
        insert_mock_1()

    def test_get_simple_model(self):
        """
        python manage.py test app.tests.test_models.ModelTestCase.test_get_simple_model
        """
        logger.info("Test get on simple lab models")

        lib_one = Library.objects.get(library_id=LIBRARY_1['library_id'], )
        self.assertEqual(lib_one.library_id, LIBRARY_1['library_id'], "incorrect 'id' from given internal library id")

        spc_one = Sample.objects.get(sample_id=SAMPLE_1['sample_id'], )
        self.assertEqual(spc_one.sample_id, SAMPLE_1['sample_id'], "incorrect 'id' from given internal sample id")

        sub_one = Subject.objects.get(subject_id=SUBJECT_1['subject_id'], )
        self.assertEqual(sub_one.subject_id, SUBJECT_1['subject_id'],
                         "incorrect 'id' from subject_id")

        cnt_one = Contact.objects.get(contact_id=CONTACT_1['contact_id'], )
        self.assertEqual(cnt_one.contact_id, CONTACT_1['contact_id'], "incorrect 'id' from given internal contact id")

        idv_one = Individual.objects.get(individual_id=INDIVIDUAL_1['individual_id'], )
        self.assertEqual(idv_one.individual_id, INDIVIDUAL_1['individual_id'],
                         "incorrect 'id' from given internal individual id")

        prj_one = Project.objects.get(project_id=PROJECT_1['project_id'], )
        self.assertEqual(prj_one.project_id, PROJECT_1['project_id'], "incorrect 'id' from given internal project id")

    def test_metadata_model_relationship(self):
        """
        python manage.py test app.tests.test_models.ModelTestCase.test_metadata_model_relationship
        """
        logger.info("Test the relationship model within the lab metadata")

        lib_one = Library.objects.get(library_id=LIBRARY_1['library_id'])

        # find the linked sample
        smp_one = lib_one.sample
        self.assertEqual(smp_one.sample_id, SAMPLE_1['sample_id'], "incorrect sample 'id' should linked to library")

        # find the linked subject
        sub_one = lib_one.subject
        self.assertEqual(sub_one.subject_id, SUBJECT_1['subject_id'],
                         "incorrect subject 'id' linked to sample")

        # find the linked individual
        idv_one = sub_one.individual_set.get(individual_id=INDIVIDUAL_1['individual_id'])
        self.assertEqual(idv_one.individual_id, INDIVIDUAL_1['individual_id'],
                         "incorrect individual 'id' linked to subject")

        # find the linked project
        prj_one = lib_one.project_set.get(project_id=PROJECT_1['project_id'])
        self.assertEqual(prj_one.project_id, PROJECT_1['project_id'], "incorrect project 'id' linked to library")

        # find the linked contact
        cnt_one = prj_one.contact_set.get(contact_id=CONTACT_1['contact_id'])
        self.assertEqual(cnt_one.contact_id, CONTACT_1['contact_id'], "incorrect contact 'id' linked to project")

    def test_upsert_method(self):
        """
        python manage.py test app.tests.test_models.ModelTestCase.test_upsert_method
        """

        # Test function with updating existing record
        updated_spc_data = {
            "sample_id": SAMPLE_1['sample_id'],
            "source": 'skin',
        }
        obj, is_created, is_updated = Sample.objects.update_or_create_if_needed(
            {"sample_id": updated_spc_data["sample_id"]},
            updated_spc_data
        )
        self.assertIsNotNone(obj, "object should not be None")
        self.assertFalse(is_created, "object should NOT be created")
        self.assertTrue(is_updated, "object should be updated")

        smp_one = Sample.objects.get(sample_id=updated_spc_data["sample_id"])
        self.assertEqual(smp_one.source, updated_spc_data['source'], "incorrect 'source' from updated specimen id")

        # Test function with creating new record
        new_spc_data = {
            "sample_id": 'SMP002',
            "source": 'RNA',
        }
        obj, is_created, is_updated = Sample.objects.update_or_create_if_needed(
            {"sample_id": new_spc_data['sample_id']},
            new_spc_data
        )
        self.assertIsNotNone(obj, "object should not be None")
        self.assertTrue(is_created, "new object should be created")
        self.assertFalse(is_updated, "new object should not be updated")
        spc_two = Sample.objects.get(sample_id=new_spc_data['sample_id'])
        self.assertEqual(spc_two.sample_id, new_spc_data["sample_id"], "incorrect specimen 'id'")
        self.assertEqual(spc_two.source, new_spc_data['source'], "incorrect 'source' from new specimen id")

        # Test if no update called if no data has changed
        with patch.object(Sample.objects, 'update_or_create', return_value=(None, False)) as mock_update_or_create:
            obj, is_created, is_updated = Sample.objects.update_or_create_if_needed(
                {"sample_id": new_spc_data['sample_id']},
                new_spc_data
            )
            mock_update_or_create.assert_not_called()
            self.assertIsNotNone(obj, "object should not be None")
            self.assertFalse(is_created, "object should not be created")
            self.assertFalse(is_updated, "object should not be updated")

    def test_model_history(self):
        """
        python manage.py test app.tests.test_models.ModelTestCase.test_model_history
        """

        # Test function with updating existing record
        updated_spc_data = {
            "sample_id": SAMPLE_1['sample_id'],
            "source": 'skin',
        }
        smp, is_created, is_updated = Sample.objects.update_or_create_if_needed(
            {"sample_id": updated_spc_data["sample_id"]},
            updated_spc_data
        )

        new_smp_record, old_smp_record = smp.history.all()
        smp_delta = new_smp_record.diff_against(old_smp_record)
        for change in smp_delta.changes:
            self.assertEqual(change.field, 'source', "incorrect field changed")
            self.assertEqual(change.old, SAMPLE_1['source'], "incorrect old value")
            self.assertEqual(change.new, updated_spc_data['source'], "incorrect new value")

        # Test function with library
        lib_one = Library.objects.get(library_id=LIBRARY_1['library_id'])

        # Create new Project record
        new_prj_data = {
            "project_id": 'prj-02',
            "name": 'test_project_2'
        }
        prj_two = Project.objects.create(**new_prj_data)

        # Test addition of project create a new history from library records
        lib_one.project_set.add(prj_two)
        lib_history = lib_one.history.all()
        self.assertGreaterEqual(len(lib_history), 2, 'no history found for library')

        def find_new_prj(relationship_array):
            for relationship in relationship_array:
                if relationship['project'] == prj_two.orcabus_id:
                    return True
            return False
        lib_delta = lib_history[0].diff_against(lib_history[1])
        for change in lib_delta.changes:
            self.assertTrue(find_new_prj(change.new), 'new project not found in relationship history')
            self.assertFalse(find_new_prj(change.old), 'old project found in relationship history')

        # Test deletion of project recorded in history
        lib_one.project_set.remove(prj_two)
        # Test addition of project create a new history from library records
        lib_history = lib_one.history.all()
        self.assertGreaterEqual(len(lib_history), 2, 'no history found for library')

        lib_delta = lib_history[0].diff_against(lib_history[1])
        for change in lib_delta.changes:
            self.assertFalse(find_new_prj(change.new), 'new project history should be up to date with current')
            self.assertTrue(find_new_prj(change.old), 'old project found should still contain project_two')