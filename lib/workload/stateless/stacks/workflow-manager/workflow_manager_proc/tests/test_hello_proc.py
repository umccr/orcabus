from workflow_manager.models.helloworld import HelloWorld
from workflow_manager_proc.lambdas import hello_proc
from workflow_manager_proc.tests.case import HelloProcUnitTestCase


class HelloProcUnitTests(HelloProcUnitTestCase):

    def test_handler(self):
        """
        python manage.py test workflow_manager_proc.tests.test_hello_proc.HelloProcUnitTests.test_handler
        """
        mock_event = {
            "key": "value"
        }
        mock_hello = HelloWorld.objects.create(text="Hi")
        resp = hello_proc.handler(mock_event, None)
        self.assertIsNotNone(resp)
