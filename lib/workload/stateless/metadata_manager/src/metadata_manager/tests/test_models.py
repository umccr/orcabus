import logging
import time

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from metadata_manager.models.metadata import Metadata
from metadata_manager.tests.factories import (
    MetadataFactory,
    TumorMetadataFactory,
    WtsTumorMetadataFactory,
    TestConstant,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MetadataModelTests(TestCase):
    def test_save_metadata(self):
        """
        python manage.py test metadata_manager.tests.test_models.MetadataModelTests.test_save_metadata
        """
        logger.info("Testing creating a new metadata object")

        mock_metadata = Metadata()
        mock_metadata.save()

        self.assertEqual(1, Metadata.objects.count())

    def test_get_metadata(self):
        """
        python manage.py test metadata_manager.tests.test_models.MetadataModelTests.test_get_metadata
        """
        logger.info("Testing get query for existing and non existing metadata")

        logger.debug("Create a mockup metadata")
        MetadataFactory()

        logger.debug("Test get specific existing metadata by library_id")
        tested_metadata = Metadata.objects.get(
            library_id=TestConstant.library_id_normal.value
        )
        self.assertEqual(
            tested_metadata.library_id,
            TestConstant.library_id_normal.value,
            "Library exist as expected.",
        )

        logger.debug("Test get specific NON-existing metadata by library_id")
        try:
            tested_metadata = Metadata.objects.get(library_id="L000-NOT-EXIST")
        except ObjectDoesNotExist:
            logger.debug(
                f"ObjectDoesNotExist exception raised which is the expected outcome"
            )

    def test_get_metadata_from_modified_library(self):
        """
        python manage.py test metadata_manager.tests.test_models.MetadataModelTests.test_get_metadata_from_modified_library
        """
        logger.info("Testing get query for modified metadata")

        mock_metadata_1 = Metadata()
        mock_metadata_1.library_id = "L001"
        mock_metadata_1.project_name = "brwn-project"  # spelling error
        mock_metadata_1.save()

        time.sleep(1)  # Some buffer time to simulate different timestamp entries

        mock_metadata_2 = Metadata()
        mock_metadata_2.library_id = "L001"
        mock_metadata_2.project_name = "brown-project"
        mock_metadata_2.save()

        query_metadata = Metadata.objects.get_by_keyword(library_id="L001")
        self.assertEqual(len(query_metadata), 1, "Expect 1 metadata returned")

        correct_metadata = query_metadata[0]
        self.assertEqual(
            correct_metadata.project_name, "brown-project", "Expect 1 metadata returned"
        )

    # NOT YET IMPLEMENT

    # def test_get_by_keyword_not_sequenced(self):
    #     # python manage.py test data_portal.models.tests.test_metadata.MetadataTestCase.test_get_by_keyword_not_sequenced
    #
    #     logger.info("Test exclusion of metadata for unsequenced libraries")
    #     TumorMetadataFactory()  # does not have a LibraryRun entry, i.e. not sequenced (yet) (tumor sample)
    #     LibraryRunFactory()  # LibraryRun entry for metadata created with MetadataFactory() (normal sample)
    #
    #     # The normal library has a LibraryRun entry, i,e. has been sequenced, therefore
    #     # we expect to find it in a full metadata search
    #     lib = Metadata.objects.get_by_keyword(library_id=TestConstant.library_id_normal.value)
    #     self.assertEqual(len(lib), 1, 'Expect metadata for normal library')
    #     # and when excluding unsequenced libraries
    #     lib = Metadata.objects.get_by_keyword(library_id=TestConstant.library_id_normal.value, sequenced=True)
    #     self.assertEqual(len(lib), 1, 'Expect metadata for normal library')
    #
    #     # The tumor library has no LibraryRun entry, i,e. has NOT been sequenced, therefore
    #     # we expect to find it in a full metadata search
    #     lib = Metadata.objects.get_by_keyword(library_id=TestConstant.library_id_tumor.value)
    #     self.assertEqual(len(lib), 1, 'Expect matadata for tumor library')
    #     # and NOT when excluding unsequenced libraries
    #     lib = Metadata.objects.get_by_keyword(library_id=TestConstant.library_id_tumor.value, sequenced=True)
    #     self.assertEqual(len(lib), 0, 'Did NOT expect metadat for tumor library (not sequenced yet)')
    #
    # def test_get_by_keyword_in_not_sequenced(self):
    #     # python manage.py test data_portal.models.tests.test_metadata.MetadataTestCase.test_get_by_keyword_in_not_sequenced
    #
    #     logger.info("Test exclusion of metadata for unsequenced libraries")
    #     TumorMetadataFactory()  # does not have a LibraryRun entry, i.e. not sequenced (yet) (tumor sample)
    #     WtsTumorMetadataFactory()  # does not have a LibraryRun entry, i.e. not sequenced (yet) (tumor sample)
    #     LibraryRunFactory()  # LibraryRun entry for metadata created with MetadataFactory() (normal sample)
    #
    #     # we expect to find both record in a full metadata search
    #     lib = Metadata.objects.get_by_keyword_in(libraries=[TestConstant.library_id_normal.value, TestConstant.wts_library_id_tumor.value])
    #     self.assertEqual(len(lib), 2, 'Expect metadata for normal library')
    #     # but only the normal sample when excluding unsequenced libraries
    #     lib = Metadata.objects.get_by_keyword_in(libraries=[TestConstant.library_id_normal.value, TestConstant.wts_library_id_tumor.value], sequenced=True)
    #     self.assertEqual(len(lib), 1, 'Expect metadata for normal library')
    #
    #     # The tumor libraries have no LibraryRun entry, i,e. have NOT been sequenced, therefore
    #     # we expect to find both in a full metadata search
    #     lib = Metadata.objects.get_by_keyword_in(libraries=[TestConstant.library_id_tumor.value, TestConstant.wts_library_id_tumor.value])
    #     self.assertEqual(len(lib), 2, 'Expect matadata for tumor library')
    #     # but none when excluding unsequenced libraries
    #     lib = Metadata.objects.get_by_keyword_in(libraries=[TestConstant.library_id_tumor.value, TestConstant.wts_library_id_tumor.value], sequenced=True)
    #     self.assertEqual(len(lib), 0, 'Did NOT expect metadat for tumor library (not sequenced yet)')
