import logging

from django.test import TestCase

from metadata_manager.models.metadata import Metadata
from metadata_manager.tests.factories import MetadataFactory, TestConstant

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MetadataViewSetTestCase(TestCase):
    def setUp(self):
        logger.debug("Create mock metadata")
        MetadataFactory()

    def test_get_api(self):
        """
        python manage.py test metadata_manager.tests.test_viewsets.MetadataViewSetTestCase.test_get_api
        """
        logger.info("Test if GET requests return the specific requested library")

        response = self.client.get("/metadata/")
        self.assertEqual(response.status_code, 200, "Ok status response is expected")

        result_response = response.data["results"]
        self.assertGreater(len(result_response), 0, "A result is expected")

        response = self.client.get(
            f"""/metadata/?library_id={TestConstant.library_id_normal.value}"""
        )
        results_response = response.data["results"]
        self.assertEqual(
            len(results_response), 1, "single result is expected for unique data"
        )
