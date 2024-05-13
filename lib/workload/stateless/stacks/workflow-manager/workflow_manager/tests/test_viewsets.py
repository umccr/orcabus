import logging

from django.test import TestCase

from workflow_manager.models.workflow import Workflow
from workflow_manager.urls.base import api_base


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WorkflowViewSetTestCase(TestCase):
    endpoint = f"/{api_base}workflow"

    def setUp(self):
        Workflow.objects.create(
            text="Bonjour le monde",
        )

    def test_get_api(self):
        """
        python manage.py test workflow_manager.tests.test_viewsets.WorkflowViewSetTestCase.test_get_api
        """
        response = self.client.get(f"{self.endpoint}/")
        logger.info(response)
        self.assertEqual(response.status_code, 200, 'Ok status response is expected')
