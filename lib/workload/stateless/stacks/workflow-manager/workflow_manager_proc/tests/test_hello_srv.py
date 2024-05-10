from workflow_manager_proc.services import hello_srv
from workflow_manager_proc.tests.case import HelloProcUnitTestCase, logger
from workflow_manager.models.helloworld import HelloWorld


class HelloSrvUnitTests(HelloProcUnitTestCase):

    def test_get_hello_from_db(self):
        """
        python manage.py test workflow_manager_proc.tests.test_hello_srv.HelloSrvUnitTests.test_get_hello_from_db
        """
        mock_hello = HelloWorld()
        mock_hello.text = "Hola Mundo"
        mock_hello.save()

        hola = hello_srv.get_hello_from_db()
        logger.info(hola)
        self.assertIsNotNone(hola)
        self.assertIn("Hola", hola.text)
