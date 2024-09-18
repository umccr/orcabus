import logging

from django.test import TestCase

from fastq_manager.urls.base import api_base
from fastq_manager.tests.factories import FastqPairFactory

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class FastqPairViewSetTestCase(TestCase):
    endpoint = f"/{api_base}fastq"

    def setUp(self):
        FastqPairFactory()

    def test_get_api(self):
        """
        python manage.py test fastq_manager.tests.test_viewsets.FastqPairViewSetTestCase.test_get_api
        """
        response = self.client.get(f"{self.endpoint}/")
        logger.info(response.json())
        self.assertEqual(response.status_code, 200, 'Ok status response is expected')
