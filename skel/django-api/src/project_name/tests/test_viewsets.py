import logging

from django.test import TestCase

from {{project_name}}.models.helloworld import HelloWorld

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class HelloViewSetTestCase(TestCase):

    def setUp(self):
        HelloWorld.objects.create(
            text="Bonjour le monde",
        )

    def test_get_api(self):
        """
        python manage.py test {{project_name}}.tests.test_viewsets.HelloViewSetTestCase.test_get_api
        """
        response = self.client.get('/hello/')
        logger.info(response.json())
        self.assertEqual(response.status_code, 200, 'Ok status response is expected')
