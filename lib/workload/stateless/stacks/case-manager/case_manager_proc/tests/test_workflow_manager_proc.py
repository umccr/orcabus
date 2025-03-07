from unittest import skip
from case_manager.models.case import Case
from case_manager_proc.lambdas import handle_service_wrsc_event
from case_manager_proc.tests.case import CaseManagerProcUnitTestCase


class CaseManagerProcUnitTests(CaseManagerProcUnitTestCase):

    @skip
    def test_handler(self):
        """
        python manage.py test case_manager_proc.tests.test_case_manager_proc.CaseManagerProcUnitTests.test_handler
        """
        # TODO: implement
        mock_event = {
            "key": "value"
        }
        mock_wfl = Case.objects.create(text="Hi")
        resp = handle_service_wrsc_event.handler(mock_event, None)
        self.assertIsNotNone(resp)
