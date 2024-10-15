import logging

from django.test import TestCase

from app.tests.factories import LIBRARY_1, SUBJECT_1, SAMPLE_1
from app.tests.utils import insert_mock_1

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def version_endpoint(ep: str):
    return "api/v1/" + ep


class LabViewSetTestCase(TestCase):
    def setUp(self):
        insert_mock_1()

    def test_get_api(self):
        """
        python manage.py test app.tests.test_viewsets.LabViewSetTestCase.test_get_api
        """

        model_to_check = [
            {
                "path": "library",
                "props": LIBRARY_1,
                "id_key": "library_id"
            },
            {
                "path": "sample",
                "props": SAMPLE_1,
                "id_key": "sample_id"
            },
            {
                "path": "subject",
                "props": SUBJECT_1,
                "id_key": "subject_id"
            }
        ]

        for model in model_to_check:
            path_id = model['path']
            id_key = model['id_key']
            path = version_endpoint(path_id)

            logger.info(f"check API path for '{path}'")
            response = self.client.get(f"/{path}/")
            self.assertEqual(response.status_code, 200,
                             "Ok status response is expected")

            result_response = response.data["results"]
            self.assertGreater(len(result_response), 0, "A result is expected")
            logger.debug("Check if unique data has a single entry")
            response = self.client.get(f"/{path}/?{id_key}={model['props'][id_key]}")
            results_response = response.data["results"]
            self.assertEqual(
                len(results_response), 1, "Single result is expected for unique data"
            )

            logger.debug("Check if wrong parameter")
            response = self.client.get(f"/{path}/?{path}_id=ERROR")
            results_response = response.data["results"]
            self.assertEqual(
                len(results_response),
                0,
                "No results are expected for unrecognized query parameter",
            )

