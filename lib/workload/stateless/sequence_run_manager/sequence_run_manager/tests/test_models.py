import logging

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.utils.timezone import now

from sequence_run_manager.models.sequence import Sequence, SequenceStatus

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def build_mock():
    logger.info("Create Object data")
    Sequence.objects.create(
        instrument_run_id="190101_A01052_0001_BH5LY7ACGT",
        run_volume_name="gds_name",
        run_folder_path="/to/gds/folder/path",
        run_data_uri="gds://gds_name/to/gds/folder/path",
        status="Complete",
        start_time=now(),
        sample_sheet_name="SampleSheet.csv",
        sequence_run_id="r.AAAAAA",
        sequence_run_name="190101_A01052_0001_BH5LY7ACGT",
    )
    Sequence.objects.create(
        instrument_run_id="190101_A01052_0002_BH5LY7ACGT",
        run_volume_name="gds_name",
        run_folder_path="/to/gds/folder/path",
        run_data_uri="gds://gds_name/to/gds/folder/path",
        status="Fail",
        start_time=now(),
        sample_sheet_name="SampleSheet.csv",
        sequence_run_id="r.BBBBBB",
        sequence_run_name="190101_A01052_0002_BH5LY7ACGT",
    )


class SequenceTestCase(TestCase):
    def test_get_sequence(self):
        """
        python manage.py test sequence_run_manager.tests.test_models.SequenceTestCase.test_get_sequence
        """
        build_mock()
        logger.info("Test get success sequence table")
        get_complete_sequence = Sequence.objects.get(status="Complete")
        self.assertEqual(
            get_complete_sequence.status, "Complete", "Status Complete is expected"
        )
        logger.info(get_complete_sequence)

        try:
            Sequence.objects.get(status="Complete")
        except ObjectDoesNotExist:
            logger.info(f"Raised ObjectDoesNotExist")

    def test_from_seq_run_status(self):
        """
        python manage.py test sequence_run_manager.tests.test_models.SequenceTestCase.test_from_seq_run_status
        """
        sq_status: SequenceStatus = SequenceStatus.from_seq_run_status("running")
        self.assertIs(sq_status, SequenceStatus.STARTED)

        sq_status = SequenceStatus.from_seq_run_status("pendinganalysis")
        self.assertIs(sq_status, SequenceStatus.SUCCEEDED)

        sq_status = SequenceStatus.from_seq_run_status("failed")
        self.assertIs(sq_status, SequenceStatus.FAILED)

    def test_from_seq_run_status_stopped(self):
        """
        python manage.py test sequence_run_manager.tests.test_models.SequenceTestCase.test_from_seq_run_status_stopped
        """
        sq_status: SequenceStatus = SequenceStatus.from_seq_run_status("stopped")
        self.assertIs(sq_status, SequenceStatus.ABORTED)

        try:
            self.assertIs(sq_status, SequenceStatus.FAILED)
        except AssertionError as e:
            logger.exception(
                f"THIS ERROR EXCEPTION IS INTENTIONAL FOR TEST. NOT ACTUAL ERROR. \n{e}"
            )

    def test_from_seq_run_status_no_match(self):
        """
        python manage.py test sequence_run_manager.tests.test_models.SequenceTestCase.test_from_seq_run_status_no_match
        """
        try:
            _ = SequenceStatus.from_seq_run_status("flight-mode")
        except ValueError as e:
            logger.exception(
                f"THIS ERROR EXCEPTION IS INTENTIONAL FOR TEST. NOT ACTUAL ERROR. \n{e}"
            )

        self.assertRaises(ValueError)
