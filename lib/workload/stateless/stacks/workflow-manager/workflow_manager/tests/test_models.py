import logging
from unittest import skip

from django.test import TestCase

from workflow_manager.models.workflow import Workflow

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WorkflowModelTests(TestCase):

    @skip
    def test_save_workflow(self):
        """
        python manage.py test workflow_manager.tests.test_models.WorkflowModelTests.test_save_workflow
        """
        # TODO: implement
        mock_wfl = Workflow()
        mock_wfl.text = "Test Workflow"
        mock_wfl.save()

        logger.info(mock_wfl)

        self.assertEqual(1, Workflow.objects.count())
