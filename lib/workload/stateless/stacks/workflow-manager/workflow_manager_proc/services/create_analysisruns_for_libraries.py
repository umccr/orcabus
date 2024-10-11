from collections import defaultdict
from typing import List

from workflow_manager.models import Analysis, AnalysisRun, AnalysisContext, Library
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO: get list of libraries (+ required metadata) from list of library IDs
# TODO: switch pairing based on subject to pairing based on Case (creating a case is someone else's responsibility)

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
    analysis_wgs_clinical: Analysis = Analysis.objects.filter(analysis_name='WGS', contexts=context_clinical).first()  # FIXME
    analysis_wgs_research: Analysis = Analysis.objects.filter(analysis_name='WGS', contexts=context_research, analysis_version='2.0').first()  # FIXME

    # FIXME: better pairing algorithm!
    pairing = defaultdict(lambda: defaultdict(list))
    for lib in libraries:
        pairing[lib['subject']][lib['phenotype']].append(lib)

    for sbj in pairing:
        if pairing[sbj]['tumor'] and pairing[sbj]['normal']:
            # noinspection PyTypeChecker
            tumor_lib_record = None
            # noinspection PyTypeChecker
            normal_lib_record = None
            if len(pairing[sbj]['tumor']) == 1:
                tumor_lib_record: Library = Library.objects.get(library_id=pairing[sbj]['tumor'][0]['library_id'])
            if len(pairing[sbj]['normal']) == 1:
                normal_lib_record: Library = Library.objects.get(library_id=pairing[sbj]['normal'][0]['library_id'])

            if not tumor_lib_record or not normal_lib_record:
                logger.info("Not a valid pairing.")
                break

            workflow = pairing[sbj]['tumor'][0]['workflow']
            context = context_clinical if workflow == 'clinical' else context_research
            analysis = analysis_wgs_clinical if workflow == 'clinical' else analysis_wgs_research
            analysis_run_name = f"automated__{analysis.analysis_name}__{context.name}__" + \
                                f"{tumor_lib_record.library_id}__{normal_lib_record.library_id} "
            ar_wgs = AnalysisRun(
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
            logger.info(f"No pairing for {sbj}.")

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
                analysis_run_name=analysis_run_name,
                status="DRAFT",
                approval_context=context,
                analysis=analysis_cttso_qs
            )
            analysis_run.save()
            analysis_run.libraries.add(lib_record)
            analysis_runs.append(analysis_run)

    return analysis_runs

