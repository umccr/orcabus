import logging
from unittest import skip

from django.test import TestCase

from workflow_manager.models import Library
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


    def test_save_library(self):
        """
        python manage.py test workflow_manager.tests.test_models.WorkflowModelTests.test_save_library
        """

        lib = Library(
            library_id="L2400001"
        )
        lib.save()
        logger.info(lib)
        self.assertEqual(1, Library.objects.count())


    def test_save_library_with_orcabus_id(self):
        """
        python manage.py test workflow_manager.tests.test_models.WorkflowModelTests.test_save_library_with_orcabus_id
        """

        lib = Library(
            library_id="L2400001",
            orcabus_id="lib.01J8ES4ZDRQAP2BN3SDYYV5PKW"
        )
        lib.save()
        logger.info(lib)
        self.assertEqual(1, Library.objects.count())
