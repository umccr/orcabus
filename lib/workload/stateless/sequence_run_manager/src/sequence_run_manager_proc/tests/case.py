import logging

from django.test import TestCase

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SequenceRunProcUnitTestCase(TestCase):
    def setUp(self) -> None:
        # some code construct that share across all test cases under lims package
        # pass for now
        pass

    def tearDown(self) -> None:
        # undo any construct done from setUp
        # pass for now
        pass


class SequenceRunProcIntegrationTestCase(TestCase):
    pass
