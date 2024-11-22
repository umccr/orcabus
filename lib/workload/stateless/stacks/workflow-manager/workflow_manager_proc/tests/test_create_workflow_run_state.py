import json
from datetime import datetime, timedelta
from typing import List

from django.db.models import QuerySet
from django.utils.timezone import make_aware

from workflow_manager.aws_event_bridge.workflowmanager.workflowrunstatechange import WorkflowRunStateChange
from workflow_manager_proc.services import create_workflow_run_state
from workflow_manager_proc.tests.case import WorkflowManagerProcUnitTestCase, logger
from workflow_manager.models import WorkflowRun, State, WorkflowRunUtil, Library
from workflow_manager.tests.factories import WorkflowRunFactory


class WorkflowSrvUnitTests(WorkflowManagerProcUnitTestCase):

    def test_create_wrsc_no_library(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_workflow_run_state.WorkflowSrvUnitTests.test_create_wrsc_no_library
        """

        test_event = {
            "portalRunId": "202405012397gatc",
            "executionId": "icav2.id.12345",
            "timestamp": "2025-05-01T09:25:44Z",
            "status": "DRAFT",
            "workflowName": "ctTSO500",
            "workflowVersion": "4.2.7",
            "workflowRunName": "ctTSO500-L000002",
            "payload": {
                "version": "0.1.0",
                "data": {
                    "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
                    "analysisId": "12345678-238c-4200-b632-d5dd8c8db94a",
                    "userReference": "540424_A01001_0193_BBBBMMDRX5_c754de_bd822f",
                    "timeCreated": "2024-05-01T10:11:35Z",
                    "timeModified": "2024-05-01T11:24:29Z",
                    "pipelineId": "bfffffff-cb27-4dfa-846e-acd6eb081aca",
                    "pipelineCode": "CTTSO500 v4_2_7",
                    "pipelineDescription": "This is an ctTSO500 workflow execution",
                    "pipelineUrn": "urn:ilmn:ica:pipeline:bfffffff-cb27-4dfa-846e-acd6eb081aca#CTTSO500_v4_2_7"
                }
            }
        }

        logger.info("Test the created WRSC event...")
        result_wrsc: WorkflowRunStateChange = create_workflow_run_state.handler(test_event, None)
        logger.info(result_wrsc)
        self.assertIsNotNone(result_wrsc)
        self.assertEqual("ctTSO500-L000002", result_wrsc.workflowRunName)
        # We don't expect any library associations here!
        self.assertIsNone(result_wrsc.linkedLibraries)

        logger.info("Test the persisted DB record...")
        wfr_qs: QuerySet = WorkflowRun.objects.all()
        self.assertEqual(1, wfr_qs.count())
        db_wfr: WorkflowRun = wfr_qs.first()
        self.assertEqual("ctTSO500-L000002", db_wfr.workflow_run_name)
        # We don't expect any library associations here!
        self.assertEqual(0, db_wfr.libraries.count())


    def test_create_wrsc_no_payload(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_workflow_run_state.WorkflowSrvUnitTests.test_create_wrsc_no_payload
        """

        test_event = {
            "portalRunId": "202405012397gatc",
            "executionId": "icav2.id.12345",
            "timestamp": "2025-05-01T09:25:44Z",
            "status": "DRAFT",
            "workflowName": "ctTSO500",
            "workflowVersion": "4.2.7",
            "workflowRunName": "ctTSO500-L000002"
        }

        logger.info("Test the created WRSC event...")
        result_wrsc: WorkflowRunStateChange = create_workflow_run_state.handler(test_event, None)
        logger.info(result_wrsc)
        self.assertIsNotNone(result_wrsc)
        self.assertEqual("ctTSO500-L000002", result_wrsc.workflowRunName)
        # We don't expect any library associations here!
        self.assertIsNone(result_wrsc.linkedLibraries)
        self.assertIsNone(result_wrsc.payload)

        logger.info("Test the persisted DB record...")
        wfr_qs: QuerySet = WorkflowRun.objects.all()
        self.assertEqual(1, wfr_qs.count())
        db_wfr: WorkflowRun = wfr_qs.first()
        self.assertEqual("ctTSO500-L000002", db_wfr.workflow_run_name)
        # We don't expect any library associations here!
        self.assertEqual(0, db_wfr.libraries.count())


    def test_create_wrsc_library(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_workflow_run_state.WorkflowSrvUnitTests.test_create_wrsc_library
        """
        # NOTE: orcabusId with and without prefix
        #       The DB records have to be generated without prefix
        #       The event records will be passed through as in the input
        library_ids = ["L000001", "L000002"]
        orcabus_ids = ["lib.01J5M2J44HFJ9424G7074NKTGN", "01J5M2JFE1JPYV62RYQEG99CP5"]
        lib_ids = [
            {
                "libraryId": library_ids[0],
                "orcabusId": orcabus_ids[0]
            },
            {
                "libraryId": library_ids[1],
                "orcabusId": orcabus_ids[1]
            }
        ]

        test_event = {
            "portalRunId": "202405012397gatc",
            "executionId": "icav2.id.12345",
            "timestamp": "2025-05-01T09:25:44Z",
            "status": "DRAFT",
            "workflowName": "ctTSO500",
            "workflowVersion": "4.2.7",
            "workflowRunName": "ctTSO500-L000002",
            "linkedLibraries": lib_ids,
            "payload": {
                "version": "0.1.0",
                "data": {
                    "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
                    "analysisId": "12345678-238c-4200-b632-d5dd8c8db94a",
                    "userReference": "540424_A01001_0193_BBBBMMDRX5_c754de_bd822f",
                    "timeCreated": "2024-05-01T10:11:35Z",
                    "timeModified": "2024-05-01T11:24:29Z",
                    "pipelineId": "bfffffff-cb27-4dfa-846e-acd6eb081aca",
                    "pipelineCode": "CTTSO500 v4_2_7",
                    "pipelineDescription": "This is an ctTSO500 workflow execution",
                    "pipelineUrn": "urn:ilmn:ica:pipeline:bfffffff-cb27-4dfa-846e-acd6eb081aca#CTTSO500_v4_2_7"
                }
            }
        }

        logger.info("Test the created WRSC event...")
        result_wrsc: WorkflowRunStateChange = create_workflow_run_state.handler(test_event, None)
        logger.info(result_wrsc)

        # ensure that all library records have been created as proper ULIDs (without prefixes)
        db_libs = Library.objects.all()
        for l in db_libs:
            self.assertTrue(len(l.orcabus_id), 26)

        self.assertIsNotNone(result_wrsc)
        self.assertEqual("ctTSO500-L000002", result_wrsc.workflowRunName)
        # We do expect 2 library associations here!
        self.assertIsNotNone(result_wrsc.linkedLibraries)
        self.assertEqual(2, len(result_wrsc.linkedLibraries))
        for lib in result_wrsc.linkedLibraries:
            self.assertTrue(lib.libraryId in library_ids)
            self.assertTrue(lib.orcabusId in orcabus_ids)

        logger.info("Test the persisted DB record...")
        wfr_qs: QuerySet = WorkflowRun.objects.all()
        self.assertEqual(1, wfr_qs.count())
        db_wfr: WorkflowRun = wfr_qs.first()
        self.assertEqual("ctTSO500-L000002", db_wfr.workflow_run_name)
        # We do expect 2 library associations here!
        self.assertEqual(2, db_wfr.libraries.count())
        for lib in db_wfr.libraries.all():
            self.assertTrue(lib.library_id in library_ids)

    def test_create_wrsc_library_exists(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_workflow_run_state.WorkflowSrvUnitTests.test_create_wrsc_library_exists
        """

        # NOTE: orcabusId with and without prefix
        #       The DB records have to be generated without prefix
        #       The event records will be passed through as in the input
        library_ids = ["L000001", "L000002"]
        orcabus_ids = ["lib.01J5M2J44HFJ9424G7074NKTGN", "01J5M2JFE1JPYV62RYQEG99CP5"]
        lib_ids = [
            {
                "libraryId": library_ids[0],
                "orcabusId": orcabus_ids[0]
            },
            {
                "libraryId": library_ids[1],
                "orcabusId": orcabus_ids[1]
            }
        ]
        for lib_id in lib_ids:
            Library.objects.create(
                library_id=lib_id["libraryId"],
                orcabus_id=lib_id["orcabusId"]
            )

        # ensure that all library records have been created as proper ULIDs (without prefixes)
        db_libs = Library.objects.all()
        for l in db_libs:
            self.assertTrue(len(l.orcabus_id), 26)

        test_event = {
            "portalRunId": "202405012397gatc",
            "executionId": "icav2.id.12345",
            "timestamp": "2025-05-01T09:25:44Z",
            "status": "DRAFT",
            "workflowName": "ctTSO500",
            "workflowVersion": "4.2.7",
            "workflowRunName": "ctTSO500-L000002",
            "linkedLibraries": lib_ids,
            "payload": {
                "version": "0.1.0",
                "data": {
                    "projectId": "bxxxxxxxx-dxxx-4xxxx-adcc-xxxxxxxxx",
                    "analysisId": "12345678-238c-4200-b632-d5dd8c8db94a",
                    "userReference": "540424_A01001_0193_BBBBMMDRX5_c754de_bd822f",
                    "timeCreated": "2024-05-01T10:11:35Z",
                    "timeModified": "2024-05-01T11:24:29Z",
                    "pipelineId": "bfffffff-cb27-4dfa-846e-acd6eb081aca",
                    "pipelineCode": "CTTSO500 v4_2_7",
                    "pipelineDescription": "This is an ctTSO500 workflow execution",
                    "pipelineUrn": "urn:ilmn:ica:pipeline:bfffffff-cb27-4dfa-846e-acd6eb081aca#CTTSO500_v4_2_7"
                }
            }
        }

        logger.info("Test the created WRSC event...")
        result_wrsc: WorkflowRunStateChange = create_workflow_run_state.handler(test_event, None)
        logger.info(result_wrsc)
        self.assertIsNotNone(result_wrsc)
        self.assertEqual("ctTSO500-L000002", result_wrsc.workflowRunName)
        # We do expect 2 library associations here!
        self.assertIsNotNone(result_wrsc.linkedLibraries)
        self.assertEqual(2, len(result_wrsc.linkedLibraries))
        for lib in result_wrsc.linkedLibraries:
            self.assertTrue(lib.libraryId in library_ids)
            self.assertTrue(lib.orcabusId in orcabus_ids)

        logger.info("Test the persisted DB record...")
        wfr_qs: QuerySet = WorkflowRun.objects.all()
        self.assertEqual(1, wfr_qs.count())
        db_wfr: WorkflowRun = wfr_qs.first()
        self.assertEqual("ctTSO500-L000002", db_wfr.workflow_run_name)
        # We do expect 2 library associations here!
        self.assertEqual(2, db_wfr.libraries.count())
        for lib in db_wfr.libraries.all():
            self.assertTrue(lib.library_id in library_ids)

    def test_get_last_state(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_workflow_run_state.WorkflowSrvUnitTests.test_get_last_state
        """

        wfr: WorkflowRun = WorkflowRunFactory()
        s1: State = State(
            timestamp=make_aware(datetime(2024, 1, 3, 23, 55, 59, 342380)),
            workflow_run=wfr,
            status='DRAFT'
        )
        s2: State = State(
            timestamp=make_aware(datetime(2024, 1, 1, 23, 55, 59, 342380)),
            workflow_run=wfr,
            status='DRAFT'
        )
        s3: State = State(
            timestamp=make_aware(datetime(2024, 1, 4, 23, 55, 59, 342380)),
            workflow_run=wfr,
            status='DRAFT'
        )
        s4: State = State(
            timestamp=make_aware(datetime(2024, 1, 2, 23, 55, 59, 342380)),
            workflow_run=wfr,
            status='DRAFT'
        )

        # Test different orders, they all have to come to the same conclusion
        states: List[State] = [s1, s2, s3, s4]
        latest: State = WorkflowRunUtil.get_latest_state(states)
        self.assertEqual(s3.timestamp, latest.timestamp)

        states: List[State] = [s4, s1, s2, s3]
        latest: State = WorkflowRunUtil.get_latest_state(states)
        self.assertEqual(s3.timestamp, latest.timestamp)

        states: List[State] = [s3, s2, s1, s4]
        latest: State = WorkflowRunUtil.get_latest_state(states)
        self.assertEqual(s3.timestamp, latest.timestamp)

        # Now test from WorkflowRun level (need to persist DB objects though)
        s1.save()
        s2.save()
        s3.save()
        s4.save()
        wfr.save()
        util = WorkflowRunUtil(wfr)
        latest = util.get_current_state()
        self.assertEqual(s3.timestamp, latest.timestamp)

        # Test we can correctly apply a time delta
        t1 = s1.timestamp
        t2 = s2.timestamp
        delta = t1 - t2  # = 2 days
        window = timedelta(hours=1)
        self.assertTrue(delta > window, "delta > 1h")
