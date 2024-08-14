from unittest import skip
from workflow_manager_proc.services import create_workflow_run
from workflow_manager_proc.tests.case import WorkflowManagerProcUnitTestCase, logger
from workflow_manager.models.workflow import Workflow


class WorkflowSrvUnitTests(WorkflowManagerProcUnitTestCase):

    # @skip
    def test_get_workflow_from_db(self):
        """
        python manage.py test workflow_manager_proc.tests.test_workflow_srv.WorkflowSrvUnitTests.test_get_workflow_from_db
        """

        test_event = {
            "portalRunId": "202405012397gatc",
            "executionId": "icav2.id.12345",
            "timestamp": "2025-05-01T09:25:44Z",
            "status": "SUCCEEDED",
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

        test_wfl = create_workflow_run.handler(test_event, None)
        logger.info(test_wfl)
        self.assertIsNotNone(test_wfl)
        self.assertEqual("ctTSO500-L000002", test_wfl.workflow_run_name)

    def test_get_workflow_from_db2(self):
        """
        python manage.py test workflow_manager_proc.tests.test_workflow_srv.WorkflowSrvUnitTests.test_get_workflow_from_db2
        """
        lib_ids = ["L000001", "L000002"]

        test_event = {
            "portalRunId": "202405012397gatc",
            "executionId": "icav2.id.12345",
            "timestamp": "2025-05-01T09:25:44Z",
            "status": "SUCCEEDED",
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

        test_wfl = create_workflow_run.handler(test_event, None)
        logger.info(test_wfl)
        self.assertIsNotNone(test_wfl)
        self.assertEqual("ctTSO500-L000002", test_wfl.workflow_run_name)
        libs = test_wfl.libraries.all()
        for lib in libs:
            self.assertIn(lib.library_id, lib_ids)
