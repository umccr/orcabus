from datetime import datetime, timezone
import logging
import time

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from library_manager.models.library import Library
from library_manager.tests.case import LibraryUnitTestCase
from library_manager.tests.factories import (
    LibraryFactory,
    TumorLibraryFactory,
    WtsTumorLibraryFactory,
    TestConstant,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LibraryModelTests(LibraryUnitTestCase):
    def test_save_library(self):
        """
        python manage.py test library_manager.tests.test_models.LibraryModelTests.test_save_library
        """
        logger.info("Testing creating a new library object")

        mock_library = Library()
        mock_library.timestamp = datetime.now(tz=timezone.utc)
        mock_library.save()

        self.assertEqual(1, Library.objects.count())

    def test_get_library(self):
        """
        python manage.py test library_manager.tests.test_models.LibraryModelTests.test_get_library
        """
        logger.info("Testing get query for existing and non existing library")

        logger.debug("Create a mockup library")
        LibraryFactory()

        logger.debug("Test get specific existing library by library_id")
        tested_library = Library.objects.get(
            library_id=TestConstant.library_id_normal.value
        )
        self.assertEqual(
            tested_library.library_id,
            TestConstant.library_id_normal.value,
            "Library exist as expected.",
        )

        logger.debug("Test get specific NON-existing library by library_id")
        try:
            tested_library = Library.objects.get(library_id="L000-NOT-EXIST")
        except ObjectDoesNotExist:
            logger.debug(
                f"ObjectDoesNotExist exception raised which is the expected outcome"
            )

    def test_get_library_from_modified_library(self):
        """
        python manage.py test library_manager.tests.test_models.LibraryModelTests.test_get_library_from_modified_library
        """
        logger.info("Testing get query for modified library")

        mock_library_1 = Library()
        mock_library_1.library_id = "L001"
        mock_library_1.timestamp = datetime.now(tz=timezone.utc)
        mock_library_1.project_name = "brwn-project"  # name typos
        mock_library_1.save()

        # Some buffer time to simulate different timestamp entries
        time.sleep(1)

        mock_library_2 = Library()
        mock_library_2.library_id = "L001"
        mock_library_2.timestamp = datetime.now(tz=timezone.utc)
        mock_library_2.project_name = "brown-project"
        mock_library_2.save()

        library = Library.objects.get_single(library_id="L001")
        self.assertEqual(
            library.project_name, "brown-project", "Expect 1 library returned"
        )

    # NOT YET IMPLEMENT

    # def test_get_by_keyword_not_sequenced(self):
    #     # python manage.py test data_portal.models.tests.test_library.LibraryTestCase.test_get_by_keyword_not_sequenced
    #
    #     logger.info("Test exclusion of library for unsequenced libraries")
    #     TumorLibraryFactory()  # does not have a LibraryRun entry, i.e. not sequenced (yet) (tumor sample)
    #     LibraryRunFactory()  # LibraryRun entry for library created with LibraryFactory() (normal sample)
    #
    #     # The normal library has a LibraryRun entry, i,e. has been sequenced, therefore
    #     # we expect to find it in a full library search
    #     lib = Library.objects.get_by_keyword(library_id=TestConstant.library_id_normal.value)
    #     self.assertEqual(len(lib), 1, 'Expect library for normal library')
    #     # and when excluding unsequenced libraries
    #     lib = Library.objects.get_by_keyword(library_id=TestConstant.library_id_normal.value, sequenced=True)
    #     self.assertEqual(len(lib), 1, 'Expect library for normal library')
    #
    #     # The tumor library has no LibraryRun entry, i,e. has NOT been sequenced, therefore
    #     # we expect to find it in a full library search
    #     lib = Library.objects.get_by_keyword(library_id=TestConstant.library_id_tumor.value)
    #     self.assertEqual(len(lib), 1, 'Expect matadata for tumor library')
    #     # and NOT when excluding unsequenced libraries
    #     lib = Library.objects.get_by_keyword(library_id=TestConstant.library_id_tumor.value, sequenced=True)
    #     self.assertEqual(len(lib), 0, 'Did NOT expect metadat for tumor library (not sequenced yet)')
    #
    # def test_get_by_keyword_in_not_sequenced(self):
    #     # python manage.py test data_portal.models.tests.test_library.LibraryTestCase.test_get_by_keyword_in_not_sequenced
    #
    #     logger.info("Test exclusion of library for unsequenced libraries")
    #     TumorLibraryFactory()  # does not have a LibraryRun entry, i.e. not sequenced (yet) (tumor sample)
    #     WtsTumorLibraryFactory()  # does not have a LibraryRun entry, i.e. not sequenced (yet) (tumor sample)
    #     LibraryRunFactory()  # LibraryRun entry for library created with LibraryFactory() (normal sample)
    #
    #     # we expect to find both record in a full library search
    #     lib = Library.objects.get_by_keyword_in(libraries=[TestConstant.library_id_normal.value, TestConstant.wts_library_id_tumor.value])
    #     self.assertEqual(len(lib), 2, 'Expect library for normal library')
    #     # but only the normal sample when excluding unsequenced libraries
    #     lib = Library.objects.get_by_keyword_in(libraries=[TestConstant.library_id_normal.value, TestConstant.wts_library_id_tumor.value], sequenced=True)
    #     self.assertEqual(len(lib), 1, 'Expect library for normal library')
    #
    #     # The tumor libraries have no LibraryRun entry, i,e. have NOT been sequenced, therefore
    #     # we expect to find both in a full library search
    #     lib = Library.objects.get_by_keyword_in(libraries=[TestConstant.library_id_tumor.value, TestConstant.wts_library_id_tumor.value])
    #     self.assertEqual(len(lib), 2, 'Expect matadata for tumor library')
    #     # but none when excluding unsequenced libraries
    #     lib = Library.objects.get_by_keyword_in(libraries=[TestConstant.library_id_tumor.value, TestConstant.wts_library_id_tumor.value], sequenced=True)
    #     self.assertEqual(len(lib), 0, 'Did NOT expect metadat for tumor library (not sequenced yet)')
