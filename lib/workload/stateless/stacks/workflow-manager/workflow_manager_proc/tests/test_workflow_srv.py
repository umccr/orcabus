from unittest import skip
from workflow_manager_proc.services import create_workflow_run
from workflow_manager_proc.tests.case import WorkflowManagerProcUnitTestCase, logger
from workflow_manager.models.workflow import Workflow


class WorkflowSrvUnitTests(WorkflowManagerProcUnitTestCase):

    @skip
    def test_get_workflow_from_db(self):
        """
        python manage.py test workflow_manager_proc.tests.test_workflow_srv.WorkflowSrvUnitTests.test_get_workflow_from_db
        """
        # TODO: implement
        mock_wfl = Workflow()
        mock_wfl.text = "Test Workflow"
        mock_wfl.save()

        test_wfl = create_workflow_run.handler()
        logger.info(test_wfl)
        self.assertIsNotNone(test_wfl)
        self.assertIn("Workflow", test_wfl.portal_run_id)
