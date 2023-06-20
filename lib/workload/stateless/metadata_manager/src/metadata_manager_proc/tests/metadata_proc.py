from metadata_manager.models.metadata import Metadata
from metadata_manager_proc.lambdas import metadata_proc
from metadata_manager_proc.tests.case import MetadataProcUnitTestCase


class ProcUnitTests(MetadataProcUnitTestCase):
    def test_handler(self):
        """
        python manage.py test metadata_manager_proc.tests.test_hello_proc.HelloProcUnitTests.test_handler
        """
        mock_event = {"key": "value"}
        mock_hello = Metadata.objects.create(text="Hi")
        resp = metadata_proc.handler(mock_event, None)
        self.assertIsNotNone(resp)
