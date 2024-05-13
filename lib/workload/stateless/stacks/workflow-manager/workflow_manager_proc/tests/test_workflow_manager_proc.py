from workflow_manager.models.workflow import Workflow
from workflow_manager_proc.lambdas import workflow_manager_proc
from workflow_manager_proc.tests.case import WorkflowManagerProcUnitTestCase


class WorkflowManagerProcUnitTests(WorkflowManagerProcUnitTestCase):

    def test_handler(self):
        """
        python manage.py test workflow_manager_proc.tests.test_workflow_manager_proc.WorkflowManagerProcUnitTests.test_handler
        """
        mock_event = {
            "key": "value"
        }
        mock_wfl = Workflow.objects.create(text="Hi")
        resp = workflow_manager_proc.handler(mock_event, None)
        self.assertIsNotNone(resp)
