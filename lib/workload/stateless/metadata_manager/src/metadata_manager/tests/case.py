import logging

from django.test import TestCase

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MetadataUnitTestCase(TestCase):
    def setUp(self) -> None:
        logger.info("\n")
        logger.info("-" * 64)
        pass

    def tearDown(self) -> None:
        pass
