import logging

from django.test import TestCase

from fastq_manager.models.fastq_pair import FastqPair
from fastq_manager.tests.factories import FastqPairFactory

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class FastqPairModelTests(TestCase):

    def test_save_fastq_pair(self):
        """
        python manage.py test fastq_manager.tests.test_models.HelloModelTests.test_save_hello
        """
        fastq_pair = FastqPairFactory()
        fastq_pair.save()

        logger.info(fastq_pair)

        self.assertEqual(1, FastqPair.objects.count())
