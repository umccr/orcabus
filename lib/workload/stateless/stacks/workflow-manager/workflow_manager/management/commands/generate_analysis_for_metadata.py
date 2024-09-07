from typing import List
import ulid
from collections import defaultdict
from django.core.management import BaseCommand
from workflow_manager.models import Workflow, Analysis, AnalysisContext, AnalysisRun, Library

# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
from workflow_manager.tests.factories import PayloadFactory, LibraryFactory


class Command(BaseCommand):
    help = """
        Generate mock data and populate DB for local testing.
        python manage.py generate_analysis_for_metadata
    """

    def handle(self, *args, **options):

        libraries = [
            {
                "phenotype": "tumor",
                "library_id": "L000001",
                "assay": "TsqNano",
                "type": "WGS",
                "subject": "SBJ00001",
                "workflow": "clinical"
            },
            {
                "phenotype": "normal",
                "library_id": "L000002",
                "assay": "TsqNano",
                "type": "WGS",
                "subject": "SBJ00001",
                "workflow": "clinical"
            },
            {
                "phenotype": "tumor",
                "library_id": "L000003",
                "assay": "TsqNano",
                "type": "WGS",
                "subject": "SBJ00002",
                "workflow": "research"
            },
            {
                "phenotype": "normal",
                "library_id": "L000004",
                "assay": "TsqNano",
                "type": "WGS",
                "subject": "SBJ00002",
                "workflow": "research"
            },
            {
                "phenotype": "tumor",
                "library_id": "L000005",
                "assay": "ctTSOv2",
                "type": "ctDNA",
                "subject": "SBJ00003",
                "workflow": "clinical"
            },
            {
                "phenotype": "tumor",
                "library_id": "L000006",
                "assay": "ctTSOv2",
                "type": "ctDNA",
                "subject": "SBJ00003",
                "workflow": "research"
            },
        ]

        # Create needed workflows
        # Create Analysis
        _setup_requirements()

        # Use metadata to decide on Analysis
        runs: List[AnalysisRun] = assign_analysis(libraries)

        print(runs)
        print("Done")


def _setup_requirements():
    """
    Create the resources assumed pre-existing. These are usually registered via external services or manual operation.
    """

    # ----- ----- ----- ----- ----- ----- ----- ----- ----- -----
    # The contexts information available for analysis

    clinical_context = AnalysisContext(
        orcabus_id="ctx.12345",
        context_id="C12345",
        name="accredited",
        description="Accredited by NATA",
        status="ACTIVE",
    )
    clinical_context.save()

    research_context = AnalysisContext(
        orcabus_id="ctx.23456",
        context_id="C23456",
        name="research",
        description="For research use",
        status="ACTIVE",
    )
    research_context.save()

    internal_context = AnalysisContext(
        orcabus_id="ctx.00001",
        context_id="C00001",
        name="internal",
        description="For internal use",
        status="ACTIVE",
    )
    internal_context.save()

    # ----- ----- ----- ----- ----- ----- ----- ----- ----- -----
    # The workflows that are available to be run

    qc_workflow = Workflow(
        workflow_name="wgts_alignment_qc",
        workflow_version="1.0",
        execution_engine="ICAv2",
        execution_engine_pipeline_id="ica.pipeline.01234",
    )
    qc_workflow.save()

    wgs_workflow = Workflow(
        workflow_name="tumor_normal",
        workflow_version="1.0",
        execution_engine="ICAv2",
        execution_engine_pipeline_id="ica.pipeline.12345",
    )
    wgs_workflow.save()

    cttsov2_workflow = Workflow(
        workflow_name="cttsov2",
        workflow_version="1.0",
        execution_engine="ICAv2",
        execution_engine_pipeline_id="ica.pipeline.23456",
    )
    cttsov2_workflow.save()

    umccrise_workflow = Workflow(
        workflow_name="umccrise",
        workflow_version="1.0",
        execution_engine="ICAv2",
        execution_engine_pipeline_id="ica.pipeline.34567",
    )
    umccrise_workflow.save()

    oa_wgs_workflow = Workflow(
        workflow_name="oncoanalyser_wgs",
        workflow_version="1.0",
        execution_engine="Nextflow",
        execution_engine_pipeline_id="nf.12345",
    )
    oa_wgs_workflow.save()

    sash_workflow = Workflow(
        workflow_name="sash",
        workflow_version="1.0",
        execution_engine="Nextflow",
        execution_engine_pipeline_id="nf.23456",
    )
    sash_workflow.save()

    # ----- ----- ----- ----- ----- ----- ----- ----- ----- -----
    # The analysis options, based on the available workflows and conditions

    qc_assessment = Analysis(
        analysis_name="QC_Assessment",
        analysis_version="1.0",
        description="Quality Control analysis for WGS and WTS",
        status="ACTIVE",
    )
    qc_assessment.save()
    qc_assessment.contexts.add(clinical_context)
    qc_assessment.contexts.add(research_context)
    qc_assessment.workflows.add(qc_workflow)

    wgs_clinical_analysis = Analysis(
        analysis_name="WGS",
        analysis_version="1.0",
        description="Analysis for WGS samples",
        status="ACTIVE",
    )
    wgs_clinical_analysis.save()
    wgs_clinical_analysis.contexts.add(clinical_context)
    wgs_clinical_analysis.contexts.add(research_context)
    wgs_clinical_analysis.workflows.add(wgs_workflow)
    wgs_clinical_analysis.workflows.add(umccrise_workflow)

    wgs_research_analysis = Analysis(
        analysis_name="WGS",
        analysis_version="2.0",
        description="Analysis for WGS samples",
        status="ACTIVE",
    )
    wgs_research_analysis.save()
    wgs_research_analysis.contexts.add(research_context)
    wgs_research_analysis.workflows.add(wgs_workflow)
    wgs_research_analysis.workflows.add(oa_wgs_workflow)
    wgs_research_analysis.workflows.add(sash_workflow)

    cttso_research_analysis = Analysis(
        analysis_name="ctTSO500",
        analysis_version="1.0",
        description="Analysis for ctTSO samples",
        status="ACTIVE",
    )
    cttso_research_analysis.save()
    cttso_research_analysis.contexts.add(research_context)
    cttso_research_analysis.contexts.add(clinical_context)
    cttso_research_analysis.workflows.add(cttsov2_workflow)

    # ----- ----- ----- ----- ----- ----- ----- ----- ----- -----
    # Generate a Payload stub and some Libraries

    generic_payload = PayloadFactory()  # Payload content is not important for now
    LibraryFactory(orcabus_id="lib.01J5M2JFE1JPYV62RYQEG99CP1", library_id="L000001"),
    LibraryFactory(orcabus_id="lib.02J5M2JFE1JPYV62RYQEG99CP2", library_id="L000002"),
    LibraryFactory(orcabus_id="lib.03J5M2JFE1JPYV62RYQEG99CP3", library_id="L000003"),
    LibraryFactory(orcabus_id="lib.03J5M2JFE1JPYV62RYQEG99CP4", library_id="L000004"),
    LibraryFactory(orcabus_id="lib.03J5M2JFE1JPYV62RYQEG99CP5", library_id="L000005"),
    LibraryFactory(orcabus_id="lib.04J5M2JFE1JPYV62RYQEG99CP6", library_id="L000006")


def assign_analysis(libraries: List[dict]) -> List[AnalysisRun]:
    analysis_runs: List[AnalysisRun] = []

    # Handle QC analysis
    analysis_runs.extend(create_qc_analysis(libraries=libraries))

    # Handle WGS analysis
    analysis_runs.extend(create_wgs_analysis(libraries=libraries))

    # Handle ctTSO analysis
    analysis_runs.extend(create_cttso_analysis(libraries=libraries))

    # handle WTS

    return analysis_runs


def create_qc_analysis(libraries: List[dict]) -> List[AnalysisRun]:
    analysis_runs: List[AnalysisRun] = []
    context_internal = AnalysisContext.objects.get_by_keyword(name="internal").first()  # FIXME
    analysis_qc_qs = Analysis.objects.get_by_keyword(analysis_name='QC_Assessment')
    analysis_qc = analysis_qc_qs.first()  # FIXME: assume there are more than one and select by latest version, etc

    for lib in libraries:
        lib_record: Library = Library.objects.get(library_id=lib['library_id'])

        # handle QC
        if lib['type'] in ['WGS', 'WTS']:
            # Create QC analysis
            analysis_run = AnalysisRun(
                analysis_run_id=f"ar.{ulid.new().str}",
                analysis_run_name=f"automated__{analysis_qc.analysis_name}__{lib_record.library_id}",
                status="DRAFT",
                approval_context=context_internal,  # FIXME: does this matter here? Internal?
                analysis=analysis_qc
            )
            analysis_run.save()
            analysis_run.libraries.add(lib_record)
            analysis_runs.append(analysis_run)

    return analysis_runs


def create_wgs_analysis(libraries: List[dict]) -> List[AnalysisRun]:
    analysis_runs: List[AnalysisRun] = []
    context_clinical = AnalysisContext.objects.get_by_keyword(name="accredited").first()  # FIXME
    context_research = AnalysisContext.objects.get_by_keyword(name="research").first()  # FIXME
    analysis_wgs_clinical: Analysis = Analysis.objects.filter(analysis_name='WGS', contexts=context_clinical).first()  # TODO: filter up front?
    analysis_wgs_research: Analysis = Analysis.objects.filter(analysis_name='WGS', contexts=context_research).first()  # TODO: filter up front?

    # FIXME: better pairing algorithm!
    pairing = defaultdict(lambda: defaultdict(list))
    for lib in libraries:
        pairing[lib['subject']][lib['phenotype']].append(lib)

    for sbj in pairing:
        if pairing[sbj]['tumor'] and pairing[sbj]['normal']:
            # noinspection PyTypeChecker
            tumor_lib_record = normal_lib_record = None
            if len(pairing[sbj]['tumor']) == 1:
                tumor_lib_record: Library = Library.objects.get(library_id=pairing[sbj]['tumor'][0]['library_id'])
            if len(pairing[sbj]['normal']) == 1:
                normal_lib_record: Library = Library.objects.get(library_id=pairing[sbj]['normal'][0]['library_id'])

            if not tumor_lib_record or not normal_lib_record:
                print("Not a valid pairing.")
                break

            workflow = pairing[sbj]['tumor'][0]['workflow']
            context = context_clinical if workflow == 'clinical' else context_research
            analysis = analysis_wgs_clinical if workflow == 'clinical' else analysis_wgs_research
            analysis_run_name = f"automated__{analysis.analysis_name}__{context.name}__" + \
                                f"{tumor_lib_record.library_id}__{normal_lib_record.library_id} "
            ar_wgs = AnalysisRun(
                analysis_run_id=f"ar.{ulid.new().str}",
                analysis_run_name=analysis_run_name,
                status="DRAFT",
                approval_context=context,
                analysis=analysis
            )
            ar_wgs.save()
            ar_wgs.libraries.add(tumor_lib_record)
            ar_wgs.libraries.add(normal_lib_record)
            analysis_runs.append(ar_wgs)
        else:
            print(f"No pairing for {sbj}.")

    return analysis_runs


def create_cttso_analysis(libraries: List[dict]) -> List[AnalysisRun]:
    analysis_runs: List[AnalysisRun] = []
    context_clinical = AnalysisContext.objects.get_by_keyword(name="accredited").first()  # FIXME
    context_research = AnalysisContext.objects.get_by_keyword(name="research").first()  # FIXME
    analysis_cttso_qs = Analysis.objects.get_by_keyword(analysis_name='ctTSO500').first()  # FIXME: allow for multiple

    for lib in libraries:
        lib_record: Library = Library.objects.get(library_id=lib['library_id'])

        # handle QC
        if lib['type'] in ['ctDNA'] and lib['assay'] in ['ctTSOv2']:
            context: AnalysisContext = context_clinical if lib['workflow'] == 'clinical' else context_research
            analysis_run_name = f"automated__{analysis_cttso_qs.analysis_name}__{context.name}__{lib_record.library_id}"
            analysis_run = AnalysisRun(
                analysis_run_id=f"ar.{ulid.new().str}",
                analysis_run_name=analysis_run_name,
                status="DRAFT",
                approval_context=context,
                analysis=analysis_cttso_qs
            )
            analysis_run.save()
            analysis_run.libraries.add(lib_record)
            analysis_runs.append(analysis_run)

    return analysis_runs
