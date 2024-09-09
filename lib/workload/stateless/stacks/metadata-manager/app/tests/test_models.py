import logging

from django.test import TestCase
import ulid

from app.models import Subject, Specimen, Library

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MetadataTestCase(TestCase):
    def setUp(self):
        subject = Subject.objects.create(
            orcabus_id=f'sbj.{ulid.new().str}',
            lab_subject_id='SBJ001',
        )
        subject.full_clean()
        subject.save()

        specimen = Specimen.objects.create(
            lab_specimen_id='SPC001',
            subject=subject,
        )
        specimen.full_clean()
        specimen.save()

        library = Library.objects.create(
            library_id='L001',
            phenotype='negative-control',
            workflow='clinical',
            quality='poor',
            type='WTS',
            assay='NebRNA',
            coverage='6.3',
            specimen=specimen,
            project_name='test_project',
            project_owner='test_owner',
        )
        library.full_clean()
        library.save()

    def test_get_simple_model(self):
        """
        python manage.py test app.tests.test_models.MetadataTestCase.test_get_simple_model
        """
        logger.info("Test get on simple lab models")

        lib_one = Library.objects.get(library_id="L001")
        self.assertEqual(lib_one.library_id, "L001", "incorrect 'id' from given internal library id")

        spc_one = Specimen.objects.get(lab_specimen_id="SPC001")
        self.assertEqual(spc_one.lab_specimen_id, "SPC001", "incorrect 'id' from given internal specimen id")

        sub_one = Subject.objects.get(lab_subject_id="SBJ001")
        self.assertEqual(sub_one.lab_subject_id, "SBJ001", "incorrect 'id' from given internal subject id")

    def test_metadata_model_relationship(self):
        """
        python manage.py test app.tests.test_models.MetadataTestCase.test_metadata_model_relationship
        """
        logger.info("Test the relationship model within the lab metadata")

        lib_one = Library.objects.get(library_id="L001")

        # find the linked specimen
        spc_one = lib_one.specimen
        self.assertEqual(spc_one.lab_specimen_id, "SPC001", "incorrect specimen 'id' should linked to library")

        # find the linked subject
        sub_one = spc_one.subject
        self.assertEqual(sub_one.lab_subject_id, "SBJ001", "incorrect subject 'id' linked to specimen")
