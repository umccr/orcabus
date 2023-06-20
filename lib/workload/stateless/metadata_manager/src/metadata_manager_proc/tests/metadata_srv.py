from metadata_manager_proc.services import metadata_srv
from metadata_manager_proc.tests.case import MetadataProcUnitTestCase, logger
from metadata_manager.models.metadata import Metadata


class MetadataSrvUnitTests(MetadataProcUnitTestCase):
    def test_get_hello_from_db(self):
        """
        python manage.py test metadata_manager_proc.tests.test_hello_srv.HelloSrvUnitTests.test_get_hello_from_db
        """
        mock_hello = Metadata()
        mock_hello.text = "Hola Mundo"
        mock_hello.save()

        hola = metadata_srv.get_hello_from_db()
        logger.info(hola)
        self.assertIsNotNone(hola)
        self.assertIn("Hola", hola.text)
