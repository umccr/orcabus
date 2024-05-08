from {{project_name}}.models.helloworld import HelloWorld
from {{project_name}}_proc.lambdas import hello_proc
from {{project_name}}_proc.tests.case import HelloProcUnitTestCase


class HelloProcUnitTests(HelloProcUnitTestCase):

    def test_handler(self):
        """
        python manage.py test {{project_name}}_proc.tests.test_hello_proc.HelloProcUnitTests.test_handler
        """
        mock_event = {
            "key": "value"
        }
        mock_hello = HelloWorld.objects.create(text="Hi")
        resp = hello_proc.handler(mock_event, None)
        self.assertIsNotNone(resp)
