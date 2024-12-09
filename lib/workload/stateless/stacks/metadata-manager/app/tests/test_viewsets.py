import json
import logging

from django.test import TestCase

from app.models import Library, Sample
from app.tests.factories import LIBRARY_1, SUBJECT_1, SAMPLE_1
from app.tests.utils import insert_mock_1, is_obj_exists

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# pragma: allowlist nextline secret
TEST_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIn0.1XOO35Ozn1XNEj_W7RFefNfJnVm7C1pm7MCEBPbCkJ4"


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

    def test_delete_api(self):
        """
        python manage.py test app.tests.test_viewsets.LabViewSetTestCase.test_delete_api
        """

        library = Library.objects.get(library_id=LIBRARY_1['library_id'])
        self.client.delete(f"/{version_endpoint(f"library/{library.orcabus_id}/")}",
                           headers={'Authorization': f'Bearer {TEST_JWT}'})
        self.assertFalse(is_obj_exists(Library, library_id=LIBRARY_1['library_id']), "Library should be deleted")

        sample = Sample.objects.get(sample_id=SAMPLE_1['sample_id'])
        self.client.delete(f"/{version_endpoint(f"sample/{sample.orcabus_id}/")}",
                           headers={'Authorization': f'Bearer {TEST_JWT}'})
        self.assertFalse(is_obj_exists(Sample, sample_id=SAMPLE_1['sample_id']), "Sample should be deleted")

    def test_patch_api(self):
        """
        python manage.py test app.tests.test_viewsets.LabViewSetTestCase.test_patch_api
        """
        new_coverage = 10.0

        library = Library.objects.get(library_id=LIBRARY_1['library_id'])

        self.assertEqual(library.coverage, LIBRARY_1['coverage'], "Coverage should be the same")
        self.client.patch(f"/{version_endpoint(f"library/{library.orcabus_id}/")}",
                                data=json.dumps({"coverage":new_coverage}),
                                headers={'Authorization': f'Bearer {TEST_JWT}', 'Content-Type': 'application/json'})
        library = Library.objects.get(library_id=LIBRARY_1['library_id'])
        self.assertEqual(library.coverage, new_coverage, "Coverage should be updated")
