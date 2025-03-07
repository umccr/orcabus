import logging
from unittest import skip

from django.test import TestCase

from case_manager.models import Library
from case_manager.models.case import Case

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CaseModelTests(TestCase):

    @skip
    def test_save_case(self):
        """
        python manage.py test case_manager.tests.test_models.CaseModelTests.test_save_case
        """
        # TODO: implement
        mock_wfl = Case()
        mock_wfl.text = "Test Case"
        mock_wfl.save()

        logger.info(mock_wfl)

        self.assertEqual(1, Case.objects.count())


    def test_save_library(self):
        """
        python manage.py test case_manager.tests.test_models.CaseModelTests.test_save_library
        """

        lib = Library(
            library_id="L2400001"
        )
        lib.save()
        logger.info(lib)
        self.assertEqual(1, Library.objects.count())


    def test_save_library_with_orcabus_id(self):
        """
        python manage.py test case_manager.tests.test_models.CaseModelTests.test_save_library_with_orcabus_id
        """

        lib = Library(
            library_id="L2400001",
            orcabus_id="lib.01J8ES4ZDRQAP2BN3SDYYV5PKW"
        )
        lib.save()
        logger.info(lib)
        self.assertEqual(1, Library.objects.count())
