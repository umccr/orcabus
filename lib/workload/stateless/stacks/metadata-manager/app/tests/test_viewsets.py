import logging

from django.test import TestCase

from app.tests.factories import LIBRARY_1, SUBJECT_1, SPECIMEN_1
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
        # Get sequence list

        model_to_check = [
            {
                "path": "library",
                "props": LIBRARY_1,
            },
            {
                "path": "specimen",
                "props": SPECIMEN_1
            },
            {
                "path": "subject",
                "props": SUBJECT_1
            }
        ]

        for model in model_to_check:
            path_id = model['path']
            path = version_endpoint(path_id)

            logger.info(f"check API path for '{path}'")
            response = self.client.get(f"/{path}/")
            self.assertEqual(response.status_code, 200,
                             "Ok status response is expected")

            result_response = response.data["results"]
            self.assertGreater(len(result_response), 0, "A result is expected")
            logger.debug("Check if unique data has a single entry")
            response = self.client.get(f"/{path}/?{path_id}_id={model['props'][f'{path_id}_id']}")
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

    def test_library_full_model_api(self):
        """
        python manage.py test app.tests.test_viewsets.LabViewSetTestCase.test_library_full_model_api
        """
        path = version_endpoint('library/full')

        logger.info(f"check API path for '{path}'")
        response = self.client.get(f"/{path}/")
        self.assertEqual(response.status_code, 200,
                         "Ok status response is expected")

        result_response = response.data["results"]
        self.assertGreater(len(result_response), 0, "A result is expected")

        logger.debug("Check if unique data has a single entry")
        response = self.client.get(f"/{path}/?library_id={LIBRARY_1['library_id']}")
        results_response = response.data["results"]
        self.assertEqual(
            len(results_response), 1, "Single result is expected for unique data"
        )

        logger.debug("check if specimen and library are linked")
        self.assertEqual(result_response[0]['specimen']['specimen_id'], SPECIMEN_1["specimen_id"], )
        self.assertEqual(result_response[0]['specimen']['subject']['subject_id'], SUBJECT_1["subject_id"], )

    def test_subject_full_model_api(self):
        """
        python manage.py test app.tests.test_viewsets.LabViewSetTestCase.test_subject_full_model_api
        """
        path = version_endpoint('subject/full')

        logger.info(f"check API path for '{path}'")
        response = self.client.get(f"/{path}/")
        self.assertEqual(response.status_code, 200,
                         "Ok status response is expected")

        result_response = response.data["results"]
        self.assertGreater(len(result_response), 0, "A result is expected")

        logger.debug("Check if unique data has a single entry")
        response = self.client.get(f"/{path}/?subject_id={SUBJECT_1['subject_id']}")
        results_response = response.data["results"]
        self.assertEqual(
            len(results_response), 1, "Single result is expected for unique data"
        )

        logger.debug("check if specimen and library are linked")
        self.assertEqual(result_response[0]['specimen_set'][0]['specimen_id'], SPECIMEN_1["specimen_id"], )
        self.assertEqual(result_response[0]['specimen_set'][0]['library_set'][0]['library_id'],
                         LIBRARY_1["library_id"], )
