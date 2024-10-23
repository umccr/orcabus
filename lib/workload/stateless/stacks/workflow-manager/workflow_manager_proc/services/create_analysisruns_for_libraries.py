import django

from workflow_manager.models.analysis import AnalysisName
from workflow_manager.models.analysis_context import Usecase, ComputeOption, StorageOption, ApprovalOption

django.setup()

# # --- keep ^^^ at top of the module
from collections import defaultdict
from typing import List

from workflow_manager.models import Analysis, AnalysisRun, AnalysisContext, Library
from workflow_manager_proc.utils import metadata_utils
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO: create internal library model and map metadata against
# TODO: switch pairing based on subject to pairing based on Case (creating a case is someone else's responsibility)

contexts = defaultdict(dict)


def handler(event, context):
    """
    Given a set of libraries (e.g. sequenced together) try to assign analysis.

    - retrieve metadata for libraries
    - assign analysis based on preconfigured rules
        - QC for (all?) FASTQ pairs
        - cttso for single FASTQ pairs that are: ctTSO, DNA, tumor
        - wgts for the same subject
            - wgs: tumor / normal DNA libraries (possibly topups)
            - wts: tumor RNA
            - wgts: results of wgs + wts


    """
    pass


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

    compute_context = get_analysis_context(Usecase.COMPUTE.value, ComputeOption.RESEARCH.value)
    storage_context = get_analysis_context(Usecase.STORAGE.value, StorageOption.TEMP.value)
    analysis = get_analysis(AnalysisName.WGTS_QC.value)

    for lib in libraries:
        lib_record: Library = Library.objects.get(library_id=lib['libraryId'])

        # handle QC
        if lib['type'] in ['WGS', 'WTS']:
            logger.debug(f"Creating QC AnalysisRun for library: {lib_record.library_id}")
            # Create QC analysis
            analysis_run = AnalysisRun(
                analysis_run_name=f"automated__{analysis.analysis_name}__{lib_record.library_id}",
                status="DRAFT",
                compute_context=compute_context,
                storage_context=storage_context,
                analysis=analysis
            )
            analysis_run.save()
            analysis_run.libraries.add(lib_record)
            analysis_runs.append(analysis_run)
        else:
            logger.debug(f"No QC AnalysisRun for library: {lib_record.library_id}")

    return analysis_runs


def create_wgs_analysis(libraries: List[dict]) -> List[AnalysisRun]:

    analysis_runs: List[AnalysisRun] = []

    # prepare the contexts and analysis we may need
    clinical_context = get_analysis_context(Usecase.APPROVAL.value, ApprovalOption.CLINICAL.value)
    compute_context_clinical = get_analysis_context(usecase=Usecase.COMPUTE.value, name=ComputeOption.ACCREDITED.value)
    compute_context_research = get_analysis_context(usecase=Usecase.COMPUTE.value, name=ComputeOption.RESEARCH.value)
    storage_context_clinical = get_analysis_context(usecase=Usecase.STORAGE.value, name=StorageOption.ACCREDITED.value)
    storage_context_research = get_analysis_context(usecase=Usecase.STORAGE.value, name=StorageOption.RESEARCH.value)
    analysis_clinical: Analysis = get_analysis(name=AnalysisName.TN.value, contexts=[clinical_context])
    analysis_research: Analysis = get_analysis(name=AnalysisName.TN.value)

    pairing = do_pairing(libraries)

    for sbj in pairing:
        if pairing[sbj]['tumor'] and pairing[sbj]['normal']:
            if len(pairing[sbj]['tumor']) == 1:
                tumor_lib_record: Library = Library.objects.get(library_id=pairing[sbj]['tumor'][0]['libraryId'])
            else:
                logger.info("Not a valid pairing. (no single normal library)")
                break
            if len(pairing[sbj]['normal']) == 1:
                normal_lib_record: Library = Library.objects.get(library_id=pairing[sbj]['normal'][0]['libraryId'])
            else:
                logger.info("Not a valid pairing. (no single tumor library)")
                break

            workflow = pairing[sbj]['tumor'][0]['workflow']
            if workflow == 'clinical':
                compute_context = compute_context_clinical
                storage_context = storage_context_clinical
                analysis = analysis_clinical
            else:
                compute_context = compute_context_research
                storage_context = storage_context_research
                analysis = analysis_research
            analysis_run_name = f"automated__{analysis.analysis_name}__{workflow}__" + \
                                f"{tumor_lib_record.library_id}__{normal_lib_record.library_id} "

            arun = AnalysisRun(
                analysis_run_name=analysis_run_name,
                status="DRAFT",
                compute_context=compute_context,
                storage_context=storage_context,
                analysis=analysis
            )
            arun.save()
            arun.libraries.add(tumor_lib_record)
            arun.libraries.add(normal_lib_record)
            analysis_runs.append(arun)
        else:
            logger.info(f"No pairing for {sbj}.")

    return analysis_runs


def do_pairing(libraries: List[dict]):
    # TODO: improve pairing algorithm
    #       improve robustness
    #       use internal lib model
    pairing = defaultdict(lambda: defaultdict(list))
    for lib in libraries:
        if lib['type'] != 'WGS':  # only pair WGS libs
            continue
        sbj = lib['subject']['subjectId']
        phenotype = lib['phenotype']
        pairing[sbj][phenotype].append(lib)

    return pairing


def create_cttso_analysis(libraries: List[dict]) -> List[AnalysisRun]:
    analysis_runs: List[AnalysisRun] = []
    nata_context = get_analysis_context(Usecase.APPROVAL.value, ApprovalOption.NATA.value)
    v1_analysis = get_analysis(name=AnalysisName.CTTSO.value, contexts=[nata_context])
    v2_analysis = get_analysis(name=AnalysisName.CTTSO.value)

    for lib in libraries:
        lib_record: Library = Library.objects.get(library_id=lib['libraryId'])

        # handle ctTSO
        if lib['type'] == 'ctDNA' and lib['assay'] in ['ctTSO', 'ctTSOv2']:
            if lib['assay'] == 'ctTSO' and lib['workflow'] == 'clinical':
                analysis = v1_analysis
            else:
                analysis = v2_analysis
            if lib['workflow'] == 'clinical':
                compute_context = get_analysis_context(Usecase.COMPUTE.value, ComputeOption.ACCREDITED.value)
                storage_context = get_analysis_context(Usecase.STORAGE.value, ComputeOption.ACCREDITED.value)
                analysis_run_name = f"automated__{analysis.analysis_name}__clinical__{lib_record.library_id}"
            else:
                compute_context = get_analysis_context(Usecase.COMPUTE.value, ComputeOption.RESEARCH.value)
                storage_context = get_analysis_context(Usecase.STORAGE.value, ComputeOption.RESEARCH.value)
                analysis_run_name = f"automated__{analysis.analysis_name}__research__{lib_record.library_id}"

            analysis_run = AnalysisRun(
                analysis_run_name=analysis_run_name,
                status="DRAFT",
                compute_context=compute_context,
                storage_context=storage_context,
                analysis=analysis
            )
            analysis_run.save()
            analysis_run.libraries.add(lib_record)
            analysis_runs.append(analysis_run)

    return analysis_runs


def get_library_details(library_ids: List[str]) -> List[dict]:
    """
    Retrieve metadata for each library that is needed to make decisions on how to analyse it.
    NOTE: the local library model could be extended to store this data

    Metadata records have the form:
    {
        "orcabusId": "lib.01J9T9C2ZJHE9EP3X50H7R4G4F",
        "projectSet": [
            {
                "orcabusId": "prj.01J9T68SYN4KQBCX39MKH8A00R",
                "projectId": "COUMN",
                "name": None,
                "description": None,
            }
        ],
        "sample": {
            "orcabusId": "smp.01J9T9C2YW53TSRFT5ZT91B684",
            "sampleId": "PRJ241640",
            "externalSampleId": "PGL29",
            "source": "blood",
        },
        "subject": {
            "orcabusId": "sbj.01J9T97D5N8B468ZEQE1PH9RT7",
            "subjectId": "PPGL29",
        },
        "libraryId": "L2401461",
        "phenotype": "normal",
        "workflow": "clinical",
        "quality": "good",
        "type": "WGS",
        "assay": "TsqNano",
        "coverage": 40.0,
    }
    """
    lib_records = metadata_utils.get_libraries(library_ids)
    return lib_records


def get_analysis_context(usecase: str, name: str) -> AnalysisContext:
    # TODO: better caching

    if not contexts[usecase] or not contexts[usecase].get(name):
        a: AnalysisContext = AnalysisContext.objects.get_by_keyword(name=name, usecase=usecase, status='ACTIVE').first()
        contexts[usecase][name] = a

    return contexts[usecase][name]


def get_analysis(name: str, contexts: List[AnalysisContext] = None) -> Analysis:
    # FIXME: better approach to selecting analysis
    # TODO: caching
    qs = Analysis.objects.get_by_keyword(analysis_name=name)
    if contexts:
        qs = qs.filter(contexts__in=contexts)
    # in case there are more than one options, take the latest one by default
    # TODO: define "latest" as newest/highest analysis_version?
    return qs.order_by('-orcabus_id').first()
