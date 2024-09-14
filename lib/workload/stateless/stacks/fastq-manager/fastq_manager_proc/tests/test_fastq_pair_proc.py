from fastq_manager.tests.factories import FastqPairFactory
from fastq_manager_proc.lambdas import fastq_pair_proc
from fastq_manager_proc.tests.case import FastqPairProcUnitTestCase


class HelloProcUnitTests(FastqPairProcUnitTestCase):

    def test_handler(self):
        """
        python manage.py test fastq_manager_proc.tests.test_hello_proc.HelloProcUnitTests.test_handler
        """
        mock_event = {
            "key": "value"
        }
        fastq_pair = FastqPairFactory()
        resp = fastq_pair_proc.handler(mock_event, None)
        self.assertIsNotNone(resp)
