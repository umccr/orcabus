from workflow_manager_proc.services import workflow_srv
from workflow_manager_proc.tests.case import WorkflowManagerProcUnitTestCase, logger
from workflow_manager.models.workflow import Workflow


class WorkflowSrvUnitTests(WorkflowManagerProcUnitTestCase):

    def test_get_workflow_from_db(self):
        """
        python manage.py test workflow_manager_proc.tests.test_workflow_srv.WorkflowSrvUnitTests.test_get_workflow_from_db
        """
        mock_wfl = Workflow()
        mock_wfl.text = "Test Workflow"
        mock_wfl.save()

        test_wfl = workflow_srv.get_workflow_from_db()
        logger.info(test_wfl)
        self.assertIsNotNone(test_wfl)
        self.assertIn("Workflow", test_wfl.text)
