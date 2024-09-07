from django.core.management import BaseCommand
from django.utils.timezone import make_aware

from datetime import datetime, timedelta
from workflow_manager.models import Workflow, Analysis, AnalysisContext, AnalysisRun


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = """
        Generate mock data and populate DB for local testing.
        python manage.py generate_analysis_for_metadata
    """

    def handle(self, *args, **options):

        metadata = [
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
        ]

        # Create needed workflows
        # Create Analysis
        _setup_requirements()

        # Use metadata to decide on Analysis
        # Create AnalysisRun
        # Create WorkflowRuns

        print("Done")


def _setup_requirements():

    clinical_context = AnalysisContext(
        orcabus_id="ctx.12345",
        context_id="C12345",
        name="NATA_Accredited",
        description="Accredited by NATA",
        status="ACTIVE",
    )
    clinical_context.save()

    research_context = AnalysisContext(
        orcabus_id="ctx.23456",
        context_id="C23456",
        name="Research",
        description="For research use",
        status="ACTIVE",
    )
    research_context.save()

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

    wgs_clinical_analysis = Analysis(
        analysis_name="Accredited_WGS",
        analysis_version="1.0",
        description="NATA accredited analysis for WGS",
        status="ACTIVE",
    )
    wgs_clinical_analysis.save()
    wgs_clinical_analysis.contexts.add(clinical_context)
    wgs_clinical_analysis.workflows.add(wgs_workflow)
    wgs_clinical_analysis.workflows.add(umccrise_workflow)

    wgs_research_analysis = Analysis(
        analysis_name="Research_WGS",
        analysis_version="1.0",
        description="Analysis for WGS research samples",
        status="ACTIVE",
    )
    wgs_research_analysis.save()
    wgs_research_analysis.contexts.add(research_context)
    wgs_research_analysis.workflows.add(wgs_workflow)
    wgs_research_analysis.workflows.add(oa_wgs_workflow)
    wgs_research_analysis.workflows.add(sash_workflow)


def _assign_workflows(metadata: dict):

    pass