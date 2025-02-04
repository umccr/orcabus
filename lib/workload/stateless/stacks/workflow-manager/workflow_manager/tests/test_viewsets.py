import logging
import os
from unittest import skip
from unittest.mock import MagicMock

from django.test import TestCase
from libumccr.aws import libeb

from workflow_manager.models import WorkflowRun
from workflow_manager.models.workflow import Workflow
from workflow_manager.tests.factories import PrimaryTestData
from workflow_manager.urls.base import api_base

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WorkflowViewSetTestCase(TestCase):
    endpoint = f"/{api_base}workflow"

    def setUp(self):
        Workflow.objects.create(
            text="Bonjour le monde",
        )

    @skip
    def test_get_api(self):
        """
        python manage.py test workflow_manager.tests.test_viewsets.WorkflowViewSetTestCase.test_get_api
        """
        # TODO: implement
        response = self.client.get(f"{self.endpoint}/")
        logger.info(response)
        self.assertEqual(response.status_code, 200, 'Ok status response is expected')


class WorkflowRunRerunViewSetTestCase(TestCase):
    endpoint = f"/{api_base}workflowrun"

    def setUp(self):
        os.environ["EVENT_BUS_NAME"] = "mock-bus"
        PrimaryTestData().setup()
        self._real_emit_event = libeb.emit_event
        libeb.emit_events = MagicMock()

    def tearDown(self) -> None:
        libeb.emit_event = self._real_emit_event

    def test_rerun_api(self):
        """
        python manage.py test workflow_manager.tests.test_viewsets.WorkflowRunRerunViewSetTestCase.test_rerun_api
        """
        wfl_run = WorkflowRun.objects.all().first()
        payload = wfl_run.states.get(status='READY').payload
        payload.data = {
            "inputs": {
                "someUri": "s3://random/prefix/",
                "dataset": "BRCA"
            },
            "engineParameters": {
                "sourceUri": f"s3:/bucket/{wfl_run.portal_run_id}/",
            }
        }
        payload.save()

        response = self.client.post(f"{self.endpoint}/{wfl_run.orcabus_id}/rerun")
        self.assertIn(response.status_code, [400], 'Workflow name associated with the workflow run is not allowed')

        # Change the workflow name to 'rnasum' as this is the only allowed workflow name for rerrun
        wfl = Workflow.objects.all().first()
        wfl.workflow_name = "rnasum"
        wfl.save()

        response = self.client.post(f"{self.endpoint}/{wfl_run.orcabus_id}/rerun", data={"dataset": "INVALID_CHOICE"})
        self.assertIn(response.status_code, [400], 'Invalid payload expected')

        response = self.client.post(f"{self.endpoint}/{wfl_run.orcabus_id}/rerun", data={"dataset": "PANCAN"})
        self.assertIn(response.status_code, [200], 'Expected a successful response')
        self.assertTrue(wfl_run.portal_run_id not in str(response.content), 'expect old portal_rub_id replaced')

        response = self.client.post(f"{self.endpoint}/{wfl_run.orcabus_id}/rerun", data={"dataset": "BRCA"})
        self.assertIn(response.status_code, [400], 'Rerun duplication with same input error expected')

        response = self.client.post(f"{self.endpoint}/{wfl_run.orcabus_id}/rerun",
                                    data={"dataset": "BRCA", "allow_duplication": True})
        self.assertIn(response.status_code, [200],
                      'Rerun with same input allowed when `allow_duplication` is set to True')
