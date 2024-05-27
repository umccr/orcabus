from unittest import skip
from workflow_manager.models.workflow import Workflow
from workflow_manager_proc.lambdas import handle_service_wrsc_event
from workflow_manager_proc.tests.case import WorkflowManagerProcUnitTestCase


class WorkflowManagerProcUnitTests(WorkflowManagerProcUnitTestCase):

    @skip
    def test_handler(self):
        """
        python manage.py test workflow_manager_proc.tests.test_workflow_manager_proc.WorkflowManagerProcUnitTests.test_handler
        """
        # TODO: implement
        mock_event = {
            "key": "value"
        }
        mock_wfl = Workflow.objects.create(text="Hi")
        resp = handle_service_wrsc_event.handler(mock_event, None)
        self.assertIsNotNone(resp)
