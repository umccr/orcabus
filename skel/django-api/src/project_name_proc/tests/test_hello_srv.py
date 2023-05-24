from {{project_name}}_proc.services import hello_srv
from {{project_name}}_proc.tests.case import HelloProcUnitTestCase, logger
from {{project_name}}.models.helloworld import HelloWorld


class HelloSrvUnitTests(HelloProcUnitTestCase):

    def test_get_hello_from_db(self):
        """
        python manage.py test {{project_name}}_proc.tests.test_hello_srv.HelloSrvUnitTests.test_get_hello_from_db
        """
        mock_hello = HelloWorld()
        mock_hello.text = "Hola Mundo"
        mock_hello.save()

        hola = hello_srv.get_hello_from_db()
        logger.info(hola)
        self.assertIsNotNone(hola)
        self.assertIn("Hola", hola.text)
