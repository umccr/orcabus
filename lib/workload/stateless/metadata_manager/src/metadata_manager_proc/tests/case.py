import logging

from django.test import TestCase

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MetadataProcUnitTestCase(TestCase):
    def setUp(self) -> None:
        logger.info("\n")
        logger.info("-" * 64)
        # some code construct that share across all test cases under lims package
        # pass for now
        pass

    def tearDown(self) -> None:
        # undo any construct done from setUp
        # pass for now
        pass


class MetadataIntegrationTestCase(TestCase):
    pass
