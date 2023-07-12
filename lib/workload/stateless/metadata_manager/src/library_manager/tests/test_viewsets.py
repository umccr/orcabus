import logging

from django.test import TestCase

from library_manager.models.library import Library
from library_manager.tests.case import LibraryUnitTestCase
from library_manager.tests.factories import LibraryFactory, TestConstant

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LibraryViewSetTestCase(LibraryUnitTestCase):
    def setUp(self):
        logger.debug("Create mock library")
        LibraryFactory()

    def test_get_api(self):
        """
        python manage.py test library_manager.tests.test_viewsets.LibraryViewSetTestCase.test_get_api
        """
        logger.info("Test if GET requests return the specific requested library\n")

        response = self.client.get("/library/")
        self.assertEqual(response.status_code, 200, "Ok status response is expected")

        result_response = response.data["results"]
        self.assertGreater(len(result_response), 0, "A result is expected")

        response = self.client.get(
            f"""/library/?library_id={TestConstant.library_id_normal.value}"""
        )
        results_response = response.data["results"]
        self.assertEqual(
            len(results_response), 1, "single result is expected for unique data"
        )
