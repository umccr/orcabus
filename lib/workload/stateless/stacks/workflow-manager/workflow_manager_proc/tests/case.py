import logging

from django.test import TestCase

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WorkflowManagerProcUnitTestCase(TestCase):

    def setUp(self) -> None:
        # some code construct that share across all test cases under lims package
        # pass for now
        pass

    def tearDown(self) -> None:
        # undo any construct done from setUp
        # pass for now
        pass


class WorkflowManagerProcIntegrationTestCase(TestCase):
    pass
