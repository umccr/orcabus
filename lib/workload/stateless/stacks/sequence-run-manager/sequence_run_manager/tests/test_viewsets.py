import logging

from django.test import TestCase
from django.utils.timezone import now

from sequence_run_manager.models.sequence import Sequence, SequenceStatus
from sequence_run_manager.urls.base import api_base

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SequenceViewSetTestCase(TestCase):
    endpoint = f"/{api_base}sequence"

    def setUp(self):
        Sequence.objects.create(
            instrument_run_id="190101_A01052_0001_BH5LY7ACGT",
            run_volume_name="gds_name",
            run_folder_path="/to/gds/folder/path",
            run_data_uri="gds://gds_name/to/gds/folder/path",
            status=SequenceStatus.from_seq_run_status("Complete"),
            start_time=now(),
            sample_sheet_name="SampleSheet.csv",
            sequence_run_id="r.AAAAAA",
            sequence_run_name="190101_A01052_0001_BH5LY7ACGT",
            api_url="https://bssh.dev/api/v1/runs/r.AAAAAA",
            v1pre3_id="1234567890",
            ica_project_id="12345678-53ba-47a5-854d-e6b53101adb7",
            experiment_name="ExperimentName",
        )

    def test_get_api(self):
        """
        python manage.py test sequence_run_manager.tests.test_viewsets.SequenceViewSetTestCase.test_get_api
        """
        # Get sequence list
        logger.info("Get sequence API")
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200, "Ok status response is expected")

        logger.info("Check if API return result")
        result_response = response.data["results"]
        self.assertGreater(len(result_response), 0, "A result is expected")

    def test_get_by_uk_surrogate_key(self):
        """
        python manage.py test sequence_run_manager.tests.test_viewsets.SequenceViewSetTestCase.test_get_by_uk_surrogate_key
        """
        logger.info("Check if unique data has a single entry")
        response = self.client.get(f"{self.endpoint}/?instrument_run_id=190101_A01052_0001_BH5LY7ACGT")
        results_response = response.data["results"]
        self.assertEqual(
            len(results_response), 1, "Single result is expected for unique data"
        )

    def test_get_by_sequence_run_id(self):
        """
        python manage.py test sequence_run_manager.tests.test_viewsets.SequenceViewSetTestCase.test_get_by_sequence_run_id
        """
        logger.info("Check if unique data has a single entry")
        response = self.client.get(f"{self.endpoint}/?sequence_run_id=r.AAAAAA")
        results_response = response.data["results"]
        self.assertEqual(
            len(results_response), 1, "Single result is expected for unique data"
        )

    def test_get_by_invalid_parameter(self):
        """
        python manage.py test sequence_run_manager.tests.test_viewsets.SequenceViewSetTestCase.test_get_by_invalid_parameter
        """
        logger.info("Check if wrong parameter")
        response = self.client.get(f"{self.endpoint}/?lib_id=LBR0001")
        results_response = response.data["results"]
        self.assertEqual(
            len(results_response),
            0,
            "No results are expected for unrecognized query parameter",
        )
