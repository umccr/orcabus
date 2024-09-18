from fastq_manager.models.fastq_pair import FastqPair
from fastq_manager_proc.lambdas import handle_fastq_event
from fastq_manager_proc.tests.case import FastqPairProcUnitTestCase


class FastqPairProcUnitTests(FastqPairProcUnitTestCase):

    def test_handler(self):
        """
        python manage.py test fastq_manager_proc.tests.test_fastq_pair_proc.FastqPairProcUnitTests.test_handler
        """
        # FIXME: update to proper event schema / model
        mock_event = {
            "rgid": "1234",
            "rgsm": "sample1",
            "rglb": "L000001",
            "read_1_id": "file.1234.r1",
            "read_2_id": "file.1234.r2"
        }

        resp = handle_fastq_event.handler(mock_event, None)
        self.assertIsNotNone(resp)

        db_records = FastqPair.objects.all()
        # We expect a single record in the DB based on the event above
        self.assertEqual(1, len(db_records))
        db_record = db_records.first()
        self.assertEqual('1234', db_record.rgid)
