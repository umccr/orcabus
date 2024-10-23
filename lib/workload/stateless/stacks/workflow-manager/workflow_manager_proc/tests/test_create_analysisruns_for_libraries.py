import copy

from django import setup

from workflow_manager.models import AnalysisContext, Analysis, Library
from workflow_manager.models.analysis import AnalysisName
from workflow_manager.models.analysis_context import Usecase, ComputeOption, StorageOption, ApprovalOption
from workflow_manager_proc.services.create_analysisruns_for_libraries import get_analysis_context, get_analysis
from workflow_manager_proc.tests.case import WorkflowManagerProcUnitTestCase, logger
from workflow_manager_proc.services import create_analysisruns_for_libraries as car


class WorkflowSrvUnitTests(WorkflowManagerProcUnitTestCase):
    mock_wgs_lib_n = {}
    mock_wgs_lib_t = {}
    mock_wts_lib = {}
    mock_cttso_lib = {}
    mock_foo_lib = {}

    def setUp(self) -> None:

        # Set up Libraries
        self.mock_wgs_lib_n = {
            "subject": {
                "subjectId": "SBJ001",
            },
            "orcabusId": "lib.0123456789ABCDEFGHJKMNPQRS",
            "libraryId": "L2400001",
            "phenotype": "normal",
            "workflow": "clinical",
            "type": "WGS",
            "assay": "TsqNano",
        }
        self.mock_wgs_lib_t = {
            "subject": {
                "subjectId": "SBJ001",
            },
            "orcabusId": "lib.0123456789ABCDEFGHJKMNPQRT",
            "libraryId": "L2400002",
            "phenotype": "tumor",
            "workflow": "clinical",
            "type": "WGS",
            "assay": "TsqNano",
        }
        self.mock_wts_lib = {
            "subject": {
                "subjectId": "SBJ001",
            },
            "orcabusId": "lib.0123456789ABCDEFGHJKMNPQRV",
            "libraryId": "L2400100",
            "phenotype": "tumor",
            "workflow": "clinical",
            "type": "WTS",
            "assay": "NebRNA",
        }
        self.mock_cttso_lib = {
            "subject": {
                "subjectId": "SBJ00X",
            },
            "orcabusId": "lib.0113456789ABCDEFGHJKMNPQRX",
            "libraryId": "L2401001",
            "phenotype": "tumor",
            "workflow": "clinical",
            "type": "ctDNA",
            "assay": "ctTSO",
        }
        self.mock_foo_lib = {
            "subject": {
                "subjectId": "SBJ00X",
            },
            "orcabusId": "lib.0123456789ABCDEFGHJKMNPQRz",
            "libraryId": "L2409999",
            "phenotype": "tumor",
            "workflow": "clinical",
            "type": "FOO",
            "assay": "NebRNA",
        }
        Library(
            library_id=self.mock_wgs_lib_n['libraryId'],
            orcabus_id=self.mock_wgs_lib_n['orcabusId'][4:]  # strip off prefix
        ).save()
        Library(
            library_id=self.mock_wgs_lib_t['libraryId'],
            orcabus_id=self.mock_wgs_lib_t['orcabusId'][4:]  # strip off prefix
        ).save()
        Library(
            library_id=self.mock_wts_lib['libraryId'],
            orcabus_id=self.mock_wts_lib['orcabusId'][4:]  # strip off prefix
        ).save()
        Library(
            library_id=self.mock_cttso_lib['libraryId'],
            orcabus_id=self.mock_cttso_lib['orcabusId'][4:]  # strip off prefix
        ).save()
        Library(
            library_id=self.mock_foo_lib['libraryId'],
            orcabus_id=self.mock_foo_lib['orcabusId'][4:]  # strip off prefix
        ).save()

        # Set up default AnalysisContext
        nata_context = AnalysisContext(
            orcabus_id="0123456789CONTEXT000000001",  # Required due to caching
            usecase=Usecase.APPROVAL.value,
            name=ApprovalOption.NATA.value,
            description="Accredited approval context",
            status="ACTIVE",
        )
        nata_context.save()

        clinical_context = AnalysisContext(
            orcabus_id="0123456789CONTEXT000000002",
            usecase=Usecase.APPROVAL.value,
            name=ApprovalOption.CLINICAL.value,
            description="Clinical approval context",
            status="ACTIVE",
        )
        clinical_context.save()

        AnalysisContext(
            orcabus_id="0123456789CONTEXT000000003",
            usecase=Usecase.COMPUTE.value,
            name=ComputeOption.ACCREDITED.value,
            description="Accredited compute environment",
            status="ACTIVE",
        ).save()

        AnalysisContext(
            orcabus_id="0123456789CONTEXT000000004",
            usecase=Usecase.COMPUTE.value,
            name=ComputeOption.RESEARCH.value,
            description="Research compute environment",
            status="ACTIVE",
        ).save()

        AnalysisContext(
            orcabus_id="0123456789CONTEXT000000005",
            usecase=Usecase.STORAGE.value,
            name=StorageOption.ACCREDITED.value,
            description="Accredited storage",
            status="ACTIVE",
        ).save()

        AnalysisContext(
            orcabus_id="0123456789CONTEXT000000006",
            usecase=Usecase.STORAGE.value,
            name=StorageOption.RESEARCH.value,
            description="Research storage",
            status="ACTIVE",
        ).save()

        AnalysisContext(
            usecase=Usecase.STORAGE.value,
            name=StorageOption.TEMP.value,
            description="Temporary storage",
            status="ACTIVE",
        ).save()

        # Set up default Analysis
        Analysis(
            analysis_name=AnalysisName.WGTS_QC.value,
            analysis_version="1.0",
            description="Quality Control analysis for WGS and WTS",
            status="ACTIVE",
        ).save()

        cttsov1 = Analysis(
            analysis_name=AnalysisName.CTTSO.value,
            analysis_version="1.0",
            description="ctTSO500 Illumina canned analysis",
            status="ACTIVE",
        )
        cttsov1.save()
        cttsov1.contexts.add(nata_context)

        Analysis(
            analysis_name=AnalysisName.CTTSO.value,
            analysis_version="2.6",
            description="ctTSO500 Illumina canned analysis",
            status="ACTIVE",
        ).save()

        tn_ana = Analysis(
            analysis_name=AnalysisName.TN.value,
            analysis_version="1.0",
            description="T/N analysis",
            status="ACTIVE",
        )
        tn_ana.save()
        tn_ana.contexts.add(clinical_context)

        Analysis(
            analysis_name=AnalysisName.TN.value,
            analysis_version="2.0",
            description="T/N analysis",
            status="ACTIVE",
        ).save()


    def test_get_analysis_context_exist(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_analysisruns_for_libraries.WorkflowSrvUnitTests.test_get_analysis_context_exist
        """
        context_name = 'clinical'
        context_usecase = 'approval'

        # Test: retrieve an AnalysisContext by usecase and name
        # Expect: expected AnalysisContext retrieved
        ctx = car.get_analysis_context(usecase=context_usecase, name=context_name)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.name, context_name)
        self.assertEqual(ctx.usecase, context_usecase)


    def test_get_analysis_context_not_exist(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_analysisruns_for_libraries.WorkflowSrvUnitTests.test_get_analysis_context_not_exist
        """
        # Test: provide non-existing usecase / name for AnalysisContext
        # Expect: expected no AnalysisContext is found
        ctx = car.get_analysis_context(usecase='random', name='random')
        self.assertIsNone(ctx)

        ctx = car.get_analysis_context(usecase=Usecase.COMPUTE.value, name='random')
        self.assertIsNone(ctx)

        ctx = car.get_analysis_context(usecase='random', name=ComputeOption.RESEARCH.value)
        self.assertIsNone(ctx)


    def test_get_analysis(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_analysisruns_for_libraries.WorkflowSrvUnitTests.test_get_analysis
        """

        # setup fixtures
        clinical_context = get_analysis_context(usecase=Usecase.APPROVAL.value, name=ApprovalOption.CLINICAL.value)
        nata_context = get_analysis_context(usecase=Usecase.APPROVAL.value, name=ApprovalOption.NATA.value)

        foo_context = AnalysisContext(
            name="foo",
            usecase="foo-use",
            description="Test context",
            status="ACTIVE",
        )
        foo_context.save()

        # Test: name of existing Analysis
        # Expect: Analysis found
        ana = car.get_analysis(name=AnalysisName.WGTS_QC.value)
        self.assertIsNotNone(ana)
        self.assertEqual(ana.analysis_name, AnalysisName.WGTS_QC.value)

        # Test: random (non-existing) name for Analysis
        # Expect: no Analysis found
        ana = car.get_analysis(name='random')
        self.assertIsNone(ana)

        # Test: existing Analysis name + non-existing context
        # Expect: no Analysis found
        ana = car.get_analysis(name=AnalysisName.WGTS_QC.value, contexts=[foo_context])
        self.assertIsNone(ana)

        # Test: name of Analysis alone
        # Expect: latest version of Analysis found
        ana = car.get_analysis(name=AnalysisName.TN.value)
        self.assertIsNotNone(ana)
        self.assertEqual(ana.analysis_name, AnalysisName.TN.value)
        self.assertEqual(ana.analysis_version, '2.0')  # expect latest version

        # Test: name of Analysis + context constraint
        # Expect: specific version of Analysis found
        ana_c = car.get_analysis(name=AnalysisName.TN.value, contexts=[clinical_context])
        self.assertIsNotNone(ana_c)
        self.assertEqual(ana_c.analysis_name, AnalysisName.TN.value)
        self.assertEqual(ana_c.analysis_version, '1.0')  # expect approved version

        self.assertIsNone(car.get_analysis(name=AnalysisName.TN.value, contexts=[nata_context]))
        ana_c.contexts.add(nata_context)

        ana = car.get_analysis(name=AnalysisName.TN.value, contexts=[nata_context])
        self.assertIsNotNone(ana)
        self.assertEqual(ana, ana_c)
        ana = car.get_analysis(name=AnalysisName.TN.value, contexts=[clinical_context,nata_context])
        self.assertIsNotNone(ana)
        self.assertEqual(ana, ana_c)


    def test_create_qc_analysis(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_analysisruns_for_libraries.WorkflowSrvUnitTests.test_create_qc_analysis
        """
        # libraries to use for testing
        # we expect only the first to get a QC analysis assigned
        mock_libs = [
            self.mock_wgs_lib_n,
            self.mock_foo_lib
        ]

        # setup fixtures
        compute_context = get_analysis_context(usecase=Usecase.COMPUTE.value, name=ComputeOption.RESEARCH.value)
        storage_context = get_analysis_context(usecase=Usecase.STORAGE.value, name=StorageOption.TEMP.value)

        qc_analysis = get_analysis(name=AnalysisName.WGTS_QC.value)

        # check we can retrieve an Analysis by name alone
        analysis_run_list = car.create_qc_analysis(mock_libs)
        self.assertIsNotNone(analysis_run_list)
        # we only expect 1 QC analysis
        self.assertEqual(len(analysis_run_list), 1)
        anr = analysis_run_list[0]
        self.assertEqual(anr.analysis, qc_analysis)
        self.assertEqual(anr.storage_context, storage_context)
        self.assertEqual(anr.compute_context, compute_context)

        associated_libs = anr.libraries.all()
        self.assertIsNotNone(associated_libs)
        self.assertEqual(len(associated_libs), 1)
        self.assertEqual(associated_libs[0].library_id, self.mock_wgs_lib_n['libraryId'])


    def test_create_cttso_analysis(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_analysisruns_for_libraries.WorkflowSrvUnitTests.test_create_cttso_analysis
        """
        # setup fixtures
        nata_context = get_analysis_context(usecase=Usecase.APPROVAL.value, name=ApprovalOption.NATA.value)
        accr_compute_context = get_analysis_context(usecase=Usecase.COMPUTE.value, name=ComputeOption.ACCREDITED.value)
        accr_storage_context = get_analysis_context(usecase=Usecase.STORAGE.value, name=StorageOption.ACCREDITED.value)
        res_compute_context = get_analysis_context(usecase=Usecase.COMPUTE.value, name=ComputeOption.RESEARCH.value)
        res_storage_context = get_analysis_context(usecase=Usecase.STORAGE.value, name=StorageOption.RESEARCH.value)

        cttsov1_analysis = get_analysis(name=AnalysisName.CTTSO.value, contexts=[nata_context])
        cttsov2_analysis = get_analysis(name=AnalysisName.CTTSO.value)

        # Test: v1 chemistry + clinical workflow
        # expect: v1 analysis + accredited envs
        mock_libs = [
            self.mock_wgs_lib_n,
            self.mock_cttso_lib
        ]

        analysis_run_list = car.create_cttso_analysis(mock_libs)
        self.assertIsNotNone(analysis_run_list)
        self.assertEqual(len(analysis_run_list), 1)
        anr = analysis_run_list[0]
        self.assertEqual(anr.analysis, cttsov1_analysis)
        self.assertEqual(anr.storage_context, accr_storage_context)
        self.assertEqual(anr.compute_context, accr_compute_context)

        # Test: v1 chemistry + research workflow
        # expect: v2 analysis + research envs
        cttso_lib_new = copy.deepcopy(self.mock_cttso_lib)
        cttso_lib_new['workflow'] = 'research'
        mock_libs = [
            self.mock_wgs_lib_n,
            cttso_lib_new
        ]

        analysis_run_list = car.create_cttso_analysis(mock_libs)
        self.assertIsNotNone(analysis_run_list)
        self.assertEqual(len(analysis_run_list), 1)
        anr = analysis_run_list[0]
        self.assertEqual(anr.analysis, cttsov2_analysis)
        self.assertEqual(anr.storage_context, res_storage_context)
        self.assertEqual(anr.compute_context, res_compute_context)

        # Test: v2 chemistry + research workflow
        # expect: v2 analysis + research envs
        cttso_lib_new = copy.deepcopy(self.mock_cttso_lib)
        cttso_lib_new['workflow'] = 'research'
        cttso_lib_new['assay'] = 'ctTSOv2'
        mock_libs = [
            self.mock_wgs_lib_n,
            cttso_lib_new
        ]

        analysis_run_list = car.create_cttso_analysis(mock_libs)
        self.assertIsNotNone(analysis_run_list)
        self.assertEqual(len(analysis_run_list), 1)
        anr = analysis_run_list[0]
        self.assertEqual(anr.analysis, cttsov2_analysis)
        self.assertEqual(anr.storage_context, res_storage_context)
        self.assertEqual(anr.compute_context, res_compute_context)

        # Test: v2 chemistry + clinical workflow
        # expect: v2 analysis + accredited envs
        cttso_lib_new = copy.deepcopy(self.mock_cttso_lib)
        cttso_lib_new['assay'] = 'ctTSOv2'
        cttso_lib_new['workflow'] = 'clinical'
        mock_libs = [
            self.mock_wgs_lib_n,
            cttso_lib_new
        ]

        analysis_run_list = car.create_cttso_analysis(mock_libs)
        self.assertIsNotNone(analysis_run_list)
        self.assertEqual(len(analysis_run_list), 1)
        anr = analysis_run_list[0]
        self.assertEqual(anr.analysis, cttsov2_analysis)
        self.assertEqual(anr.storage_context, accr_storage_context)
        self.assertEqual(anr.compute_context, accr_compute_context)


    def test_create_wgs_analysis(self):
        """
        python manage.py test workflow_manager_proc.tests.test_create_analysisruns_for_libraries.WorkflowSrvUnitTests.test_create_wgs_analysis
        """
        # setup fixtures
        clinical_context = get_analysis_context(usecase=Usecase.APPROVAL.value, name=ApprovalOption.CLINICAL.value)
        accr_compute_context = get_analysis_context(usecase=Usecase.COMPUTE.value, name=ComputeOption.ACCREDITED.value)
        accr_storage_context = get_analysis_context(usecase=Usecase.STORAGE.value, name=StorageOption.ACCREDITED.value)
        res_compute_context = get_analysis_context(usecase=Usecase.COMPUTE.value, name=ComputeOption.RESEARCH.value)
        res_storage_context = get_analysis_context(usecase=Usecase.STORAGE.value, name=StorageOption.RESEARCH.value)

        accr_analysis = get_analysis(name=AnalysisName.TN.value, contexts=[clinical_context])
        res_analysis = get_analysis(name=AnalysisName.TN.value)

        # Test: given a tumor and normal WGS pair + clinical workflow
        # expect: a single WGS analysis + accredited envs
        mock_libs = [
            self.mock_wgs_lib_n,
            self.mock_wgs_lib_t,
            self.mock_wts_lib
        ]

        analysis_run_list = car.create_wgs_analysis(mock_libs)
        self.assertIsNotNone(analysis_run_list)
        self.assertEqual(len(analysis_run_list), 1)
        anr = analysis_run_list[0]
        self.assertEqual(anr.analysis, accr_analysis)
        self.assertEqual(anr.storage_context, accr_storage_context)
        self.assertEqual(anr.compute_context, accr_compute_context)

        associated_libs = anr.libraries.all()
        self.assertIsNotNone(associated_libs)
        self.assertEqual(len(associated_libs), 2)
        self.assertIn(associated_libs[0].library_id, [self.mock_wgs_lib_n['libraryId'], self.mock_wgs_lib_t['libraryId']])
        self.assertIn(associated_libs[1].library_id, [self.mock_wgs_lib_n['libraryId'], self.mock_wgs_lib_t['libraryId']])

        # Test: given a tumor and normal WGS pair + research workflow (tumor)
        # expect: a single WGS analysis + research envs
        wgs_lib_t_new = copy.deepcopy(self.mock_wgs_lib_t)
        wgs_lib_t_new['workflow'] = 'research'
        mock_libs = [
            self.mock_wgs_lib_n,
            wgs_lib_t_new,
            self.mock_wts_lib
        ]

        analysis_run_list = car.create_wgs_analysis(mock_libs)
        self.assertIsNotNone(analysis_run_list)
        self.assertEqual(len(analysis_run_list), 1)
        anr = analysis_run_list[0]
        self.assertEqual(anr.analysis, res_analysis)
        self.assertEqual(anr.storage_context, res_storage_context)
        self.assertEqual(anr.compute_context, res_compute_context)

        associated_libs = anr.libraries.all()
        self.assertIsNotNone(associated_libs)
        self.assertEqual(len(associated_libs), 2)
        self.assertIn(associated_libs[0].library_id, [self.mock_wgs_lib_n['libraryId'], wgs_lib_t_new['libraryId']])
        self.assertIn(associated_libs[1].library_id, [self.mock_wgs_lib_n['libraryId'], wgs_lib_t_new['libraryId']])

        # Test: given a tumor and normal WGS non-pair (subject mismatch)
        # expect: no analysis assigned
        wgs_lib_t_new = copy.deepcopy(self.mock_wgs_lib_t)
        wgs_lib_t_new['subject']['subjectId'] = 'random'  # Overwrite (matching) subject to create subject mismatch
        mock_libs = [
            self.mock_wgs_lib_n,
            wgs_lib_t_new,
            self.mock_wts_lib
        ]

        analysis_run_list = car.create_wgs_analysis(mock_libs)
        self.assertEqual(len(analysis_run_list), 0)


