import logging
from unittest import skip

from django.test import TestCase

from case_manager.models.case import Case
from case_manager.urls.base import api_base


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CaseViewSetTestCase(TestCase):
    endpoint = f"/{api_base}case"

    def setUp(self):
        Case.objects.create(
            text="Bonjour le monde",
        )

    @skip
    def test_get_api(self):
        """
        python manage.py test case_manager.tests.test_viewsets.CaseViewSetTestCase.test_get_api
        """
        # TODO: implement
        response = self.client.get(f"{self.endpoint}/")
        logger.info(response)
        self.assertEqual(response.status_code, 200, 'Ok status response is expected')
