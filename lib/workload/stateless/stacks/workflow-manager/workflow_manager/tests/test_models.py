import logging

from django.test import TestCase

from workflow_manager.models.helloworld import HelloWorld

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class HelloModelTests(TestCase):

    def test_save_hello(self):
        """
        python manage.py test workflow_manager.tests.test_models.HelloModelTests.test_save_hello
        """
        mock_hello = HelloWorld()
        mock_hello.text = "Hello World"
        mock_hello.save()

        logger.info(mock_hello)

        self.assertEqual(1, HelloWorld.objects.count())
