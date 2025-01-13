import json
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from app.models import Subject, Library, Sample, Individual, Project, Contact
from app.tests.utils import clear_all_data
from proc.service.tracking_sheet_srv import sanitize_lab_metadata_df, persist_lab_metadata
from proc.tests.test_tracking_sheet_srv import RECORD_1, RECORD_2, RECORD_3, SHEET_YEAR


class Command(BaseCommand):
    """
    python manage.py insert_mock_data
    """
    help = "Generate mock Metadata into database for local development and testing"

    def handle(self, *args, **options):
        clear_all_data()
        load_mock_from_wfm()


def load_mock_from_proc():
    """Not in use for now, as loading data from wfm is preferred to sync data"""
    mock_sheet_data = [RECORD_1, RECORD_2, RECORD_3]

    metadata_pd = pd.json_normalize(mock_sheet_data)
    metadata_pd = sanitize_lab_metadata_df(metadata_pd)
    result = persist_lab_metadata(metadata_pd, SHEET_YEAR, is_emit_eb_events=False)

    print(json.dumps(result, indent=4))
    print("insert mock data completed")


def load_mock_from_wfm():
    # The libraries are taken from WFM as of 16/10/2024
    # Will sync this so test data sync across MM <=> WFM
    libraries = [
        {
            "orcabus_id": "01J5M2JFE1JPYV62RYQEG99CP1",
            "phenotype": "tumor",
            "library_id": "L000001",
            "assay": "TsqNano",
            "type": "WGS",
            "subject": "SBJ00001",
            "workflow": "clinical",
            "override_cycles": "Y151;I8N2;I8N2;Y151"
        },
        {
            "orcabus_id": "02J5M2JFE1JPYV62RYQEG99CP2",
            "phenotype": "normal",
            "library_id": "L000002",
            "assay": "TsqNano",
            "type": "WGS",
            "subject": "SBJ00001",
            "workflow": "clinical",
            "override_cycles": "Y151;I8N2;I8N2;Y151"
        },
        {
            "orcabus_id": "03J5M2JFE1JPYV62RYQEG99CP3",
            "phenotype": "tumor",
            "library_id": "L000003",
            "assay": "TsqNano",
            "type": "WGS",
            "subject": "SBJ00002",
            "workflow": "research",
            "override_cycles": "Y151;I8N2;I8N2;Y151"
        },
        {
            "orcabus_id": "04J5M2JFE1JPYV62RYQEG99CP4",
            "phenotype": "normal",
            "library_id": "L000004",
            "assay": "TsqNano",
            "type": "WGS",
            "subject": "SBJ00002",
            "workflow": "research",
            "override_cycles": "Y151;I8N2;I8N2;Y151"
        },
        {
            "orcabus_id": "05J5M2JFE1JPYV62RYQEG99CP5",
            "phenotype": "tumor",
            "library_id": "L000005",
            "assay": "ctTSOv2",
            "type": "ctDNA",
            "subject": "SBJ00003",
            "workflow": "clinical",
            "override_cycles": "U7N1Y143;I8;I8;U7N1Y143"
        },
        {
            "orcabus_id": "06J5M2JFE1JPYV62RYQEG99CP6",
            "phenotype": "tumor",
            "library_id": "L000006",
            "assay": "ctTSOv2",
            "type": "ctDNA",
            "subject": "SBJ00003",
            "workflow": "research",
            "override_cycles": "U7N1Y143;I8;I8;U7N1Y143"
        },
    ]

    for lib in libraries:
        idv, is_idv_created, is_idv_updated = Individual.objects.update_or_create_if_needed(
            search_key={
                "individual_id": 'IDV0001',
                "source": "lab"
            },
            data={
                "individual_id": 'IDV0001',
                "source": "lab"
            }
        )

        subject, is_sub_created, is_sub_updated = Subject.objects.update_or_create_if_needed(
            search_key={"subject_id": lib["subject"]},
            data={
                "subject_id": lib["subject"],
            }
        )

        try:
            subject.individual_set.get(orcabus_id=idv.orcabus_id)
        except ObjectDoesNotExist:
            subject.individual_set.add(idv)

        sample, is_smp_created, is_smp_updated = Sample.objects.update_or_create_if_needed(
            search_key={"sample_id": f"""smp-{lib["library_id"]}"""},
            data={
                "sample_id": f"""smp-{lib["library_id"]}""",
                "external_sample_id": f"""ext-smp-{lib["library_id"]}""",
                "source": "blood",
            }
        )

        contact, is_ctc_created, is_ctc_updated = Contact.objects.update_or_create_if_needed(
            search_key={"contact_id": 'ctc-1'},
            data={
                "contact_id": 'ctc-1',
            }
        )

        project, is_prj_created, is_prj_updated = Project.objects.update_or_create_if_needed(
            search_key={"project_id": 'prj-1'},
            data={
                "project_id": 'prj-1',
            }
        )

        try:
            project.contact_set.get(orcabus_id=contact.orcabus_id)
        except ObjectDoesNotExist:
            project.contact_set.add(contact)

        library, is_lib_created, is_lib_updated = Library.objects.update_or_create_if_needed(
            search_key={'library_id': lib["library_id"]},
            data={
                "orcabus_id": lib["orcabus_id"],
                "library_id": lib["library_id"],
                "phenotype": lib["phenotype"],
                "assay": lib["assay"],
                "type": lib["type"],
                "workflow": lib["workflow"],

                "subject_id": subject.orcabus_id,
                "sample_id": sample.orcabus_id,
            }

        )

        try:
            library.project_set.get(orcabus_id=project.orcabus_id)
        except ObjectDoesNotExist:
            library.project_set.add(project)
