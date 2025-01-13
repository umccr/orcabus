import os
import json
import pandas as pd
from libumccr.aws import libeb

from unittest.mock import MagicMock
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from app.models import Library, Sample, Subject, Project, Contact, Individual
from proc.service.tracking_sheet_srv import sanitize_lab_metadata_df, persist_lab_metadata, \
    drop_incomplete_tracking_sheet_records
from .utils import check_put_event_entries_format, check_put_event_value, is_expected_event_in_output

TEST_EVENT_BUS_NAME = "TEST_BUS"

SHEET_YEAR = "2010"

RECORD_1 = {
    "LibraryID": "L10001",
    "SampleID": "PRJ10001",
    "ExternalSampleID": "EXT_PRJ10001",
    "SubjectID": "SBJ001",
    "ExternalSubjectID": "EXT_SBJ001",
    "Phenotype": "normal",
    "Quality": "good",
    "Source": "blood",
    "ProjectOwner": "UMCCR",
    "ProjectName": "Research",
    "ExperimentID": "",
    "Type": "WTS",
    "Assay": "ctTSO",
    "OverrideCycles": "Y147;I8U11;I8N2;Y147",
    "Workflow": "research",
    "Coverage (X)": "120",
    "TruSeq Index, unless stated": "",
    "Run#": "P100",
    "Comments": "",
    "qPCR ID": "L1001_PRJ1001-IN_RUN_1",
    "Sample_ID (SampleSheet)": "PRJ10001_L10001",
    "SampleName": "PRJ10001-IN_RUN_1",
    "rRNA": ""
}
RECORD_2 = {
    "LibraryID": "L10002",
    "SampleID": "PRJ10001",
    "ExternalSampleID": "EXT_PRJ10001",
    "SubjectID": "SBJ001",
    "ExternalSubjectID": "EXT_SBJ001",
    "Phenotype": "tumor",
    "Quality": "good",
    "Source": "blood",
    "ProjectOwner": "UMCCR",
    "ProjectName": "Research",
    "ExperimentID": "",
    "Type": "WTS",
    "Assay": "ctTSO",
    "OverrideCycles": "Y151;I8U12;I8;Y151",
    "Workflow": "research",
    "Coverage (X)": "25.25",
    "TruSeq Index, unless stated": "",
    "Run#": "P101",
    "Comments": "",
    "qPCR ID": "L10002_PRJ10001-IN_RUN6_2",
    "Sample_ID (SampleSheet)": "L10001_PRJ10002",
    "SampleName": "PRJ10002-IN_RUN_2",
    "rRNA": ""
}
RECORD_3 = {
    "LibraryID": "L10003",
    "SampleID": "PRJ10003",
    "ExternalSampleID": "EXT_PRJ10003",
    "SubjectID": "SBJ001",
    "ExternalSubjectID": "EXT_SBJ001",
    "Phenotype": "tumor",
    "Quality": "good",
    "Source": "DNA",
    "ProjectOwner": "UMCCR",
    "ProjectName": "clinical",
    "ExperimentID": "",
    "Type": "ctTSO",
    "Assay": "ctTSO",
    "OverrideCycles": "Y151;I8U12;I8;Y151",
    "Workflow": "research",
    "Coverage (X)": "75",
    "TruSeq Index, unless stated": "",
    "Run#": "P101",
    "Comments": "",
    "qPCR ID": "L10003_PRJ10003-IN_RUN6_2",
    "Sample_ID (SampleSheet)": "L10003_PRJ10003",
    "SampleName": "PRJ10003-IN_RUN_2",
    "rRNA": ""
}


class TrackingSheetSrvUnitTests(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self._real_dispatch_events = libeb.dispatch_events
        libeb.dispatch_events = MagicMock()

    def tearDown(self) -> None:
        libeb.dispatch_events = self._real_dispatch_events
        super().tearDown()

    def test_persist_lab_metadata(self):
        """
        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_persist_lab_metadata
        """
        mock_sheet_data = [RECORD_1, RECORD_2, RECORD_3]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        result = persist_lab_metadata(metadata_pd, SHEET_YEAR)

        # Stats check
        self.assertEqual(result.get("invalid_record_count"), 0, "non invalid record should exist")
        self.assertEqual(result.get("library").get("create_count"), 3, "3 new library should be created")
        self.assertEqual(result.get("library").get("update_count"), 0, "0 update in library")
        self.assertEqual(result.get("sample").get("create_count"), 2, "2 new sample should be created")
        self.assertEqual(result.get("sample").get("update_count"), 0, "no update in sample")
        self.assertEqual(result.get("subject").get("create_count"), 1, "1 new subject should be created")
        self.assertEqual(result.get("subject").get("update_count"), 0, "no update in subject")

        lib_1 = Library.objects.get(library_id=RECORD_1.get("LibraryID"))
        self.assertEqual(lib_1.override_cycles, RECORD_1.get("OverrideCycles"),
                         "incorrect value (OverrideCycles) stored")
        self.assertEqual(lib_1.type, RECORD_1.get("Type"), "incorrect value (Type) stored")
        self.assertEqual(lib_1.phenotype, RECORD_1.get("Phenotype"), "incorrect value (Phenotype) stored")
        self.assertEqual(lib_1.assay, RECORD_1.get("Assay"), "incorrect value (Assay) stored")
        self.assertEqual(lib_1.workflow, RECORD_1.get("Workflow"), "incorrect value (Workflow) stored")
        self.assertEqual(lib_1.sample.sample_id, RECORD_1.get("SampleID"), "incorrect sample linked")

        smp_1 = Sample.objects.get(sample_id=RECORD_1.get("SampleID"))
        self.assertIsNotNone(smp_1)
        self.assertEqual(smp_1.source, RECORD_1.get("Source"), "incorrect value stored")
        self.assertEqual(smp_1.external_sample_id, RECORD_1.get("ExternalSampleID"), "incorrect value stored")

        sbj_1 = Subject.objects.get(subject_id=RECORD_1.get("ExternalSubjectID"))
        self.assertIsNotNone(sbj_1)
        self.assertEqual(sbj_1.subject_id, RECORD_1.get("ExternalSubjectID"), "incorrect value stored")

        idv_1 = Individual.objects.get(individual_id=RECORD_1.get("SubjectID"))
        self.assertIsNotNone(idv_1)
        self.assertEqual(idv_1.individual_id, RECORD_1.get("SubjectID"), "incorrect value stored")

        ctc_1 = Contact.objects.get(contact_id=RECORD_1.get("ProjectOwner"))
        self.assertIsNotNone(ctc_1)
        self.assertEqual(ctc_1.contact_id, RECORD_1.get("ProjectOwner"), "incorrect value (ProjectOwner) stored")

        prj_1 = Project.objects.get(project_id=RECORD_1.get("ProjectName"))
        self.assertIsNotNone(prj_1)
        self.assertEqual(prj_1.project_id, RECORD_1.get("ProjectName"), "incorrect value (ProjectName) stored")

        # check all relationships from each record
        for rec in mock_sheet_data:
            lib = Library.objects.get(library_id=rec.get("LibraryID"))

            ext_sbj = lib.subject
            self.assertEqual(ext_sbj.subject_id, rec.get("ExternalSubjectID"),
                             'incorrect library-subject link')

            smp = lib.sample
            self.assertEqual(smp.sample_id, rec.get("SampleID"), 'incorrect library-sample link')

            idv = ext_sbj.individual_set.get(individual_id=rec.get("SubjectID"))
            self.assertEqual(idv.individual_id, rec.get("SubjectID"), 'incorrect subject-individual link')

            prj = lib.project_set.get(project_id=rec.get("ProjectName"))
            self.assertEqual(prj.project_id, rec.get("ProjectName"), 'incorrect library-project link')

            ctc = prj.contact_set.get(contact_id=rec.get("ProjectOwner"))
            self.assertEqual(ctc.contact_id, rec.get("ProjectOwner"), 'incorrect project-contact link')

    def test_new_df_in_different_year(self) -> None:
        """
        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_new_df_in_different_year
        """

        metadata_pd = pd.json_normalize([RECORD_1])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        new_lib_id = 'L24001'
        mock_record = RECORD_1.copy()
        mock_record['LibraryID'] = new_lib_id
        metadata_pd = pd.json_normalize([mock_record])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, '2024')

        lib_all = Library.objects.all()
        self.assertEqual(lib_all.count(), 2, "2 library should be created")

        lib_1 = Library.objects.get(library_id=RECORD_1.get("LibraryID"))
        self.assertIsNotNone(lib_1)

        lib_change = Library.objects.get(library_id=new_lib_id)
        self.assertIsNotNone(lib_change)

    def test_alter_sbj_smp(self):
        """
        test where lib moved to different subject and sample

        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_alter_sbj_smp
        """

        metadata_pd = pd.json_normalize([RECORD_3])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        lib_3 = Library.objects.get(library_id=RECORD_3['LibraryID'])
        self.assertEqual(lib_3.sample.sample_id, RECORD_3['SampleID'], 'incorrect link between lib and smp')
        self.assertEqual(lib_3.subject.subject_id, RECORD_3['ExternalSubjectID'],
                         'incorrect link between lib and sbj')
        idv_3 = lib_3.subject.individual_set.get(individual_id=RECORD_3['SubjectID'])
        self.assertIsNotNone(idv_3)
        self.assertEqual(lib_3.subject.individual_set.count(), 1, 'only 1 individual should be linked')

        # Change smp and sample
        record_3_altered = {
            **RECORD_3,
            "ExternalSubjectID": "EXT_SBJ004",
            "SampleID": "PRJ10004",
        }

        metadata_pd = pd.json_normalize([record_3_altered])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        lib_3_altered = Library.objects.get(library_id=record_3_altered['LibraryID'])
        self.assertEqual(lib_3_altered.sample.sample_id, record_3_altered['SampleID'],
                         'incorrect link between lib and smp')
        self.assertEqual(lib_3_altered.subject.subject_id, record_3_altered['ExternalSubjectID'],
                         'incorrect link between lib and sbj')
        idv_3 = lib_3_altered.subject.individual_set.all()
        self.assertIsNotNone(idv_3)
        self.assertEqual(lib_3_altered.subject.individual_set.count(), 1, 'only 1 individual should be linked')

    def test_alter_idv_prj_ctc(self):
        """
        test where object is move betweeb many-to-many relationship (idv, prj, ctc)

        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_alter_idv_prj_ctc
        """

        metadata_pd = pd.json_normalize([RECORD_3])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        sbj_3 = Subject.objects.get(subject_id=RECORD_3['ExternalSubjectID'])
        self.assertIsNotNone(sbj_3)
        self.assertEqual(sbj_3.individual_set.count(), 1, 'only 1 individual should be linked')
        idv_3 = sbj_3.individual_set.get(individual_id=RECORD_3['SubjectID'])
        self.assertIsNotNone(idv_3)

        # Change individual id
        record_3_altered = {
            **RECORD_3,
            "SubjectID": "SBJ004",
            "ProjectOwner": "Doe",
            "ProjectName": "test",
        }

        metadata_pd = pd.json_normalize([record_3_altered])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        # We don't unlink previous many-to-many relationships, but only add new ones
        sbj_3 = Subject.objects.get(subject_id=record_3_altered['ExternalSubjectID'])
        idv_3 = sbj_3.individual_set.get(individual_id=record_3_altered['SubjectID'])
        self.assertIsNotNone(idv_3)

        prj_3 = Library.objects.get(library_id=record_3_altered['LibraryID']).project_set.get(
            project_id=record_3_altered['ProjectName'])
        self.assertIsNotNone(prj_3)

        ctc_3 = prj_3.contact_set.get(contact_id=record_3_altered['ProjectOwner'])
        self.assertIsNotNone(ctc_3)

    def test_with_deleted_model(self) -> None:
        """
        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_with_deleted_model
        """
        mock_sheet_data = [RECORD_1, RECORD_2, RECORD_3]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        mock_sheet_data = [RECORD_3]
        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        result = persist_lab_metadata(metadata_pd, SHEET_YEAR)

        deleted_lib = Library.objects.filter(library_id__in=[RECORD_1.get('LibraryID'), RECORD_2.get('LibraryID')])
        self.assertEqual(deleted_lib.count(), 0, 'these library query should all be deleted')
        self.assertEqual(result.get("library").get("delete_count"), 2, "2 library should be deleted")

    def test_skip_incomplete_records(self) -> None:
        """
        python manage.py test \
        proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_skip_incomplete_records
        """

        mock_record = RECORD_1.copy()
        mock_record['SubjectID'] = ''
        mock_sheet_data = [mock_record]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        metadata_pd = drop_incomplete_tracking_sheet_records(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        def is_library_exists(library_id):
            try:
                Library.objects.get(library_id=library_id)
                return True
            except ObjectDoesNotExist:
                return False

        self.assertFalse(is_library_exists(RECORD_1.get("LibraryID")), "library should not be created")

    def test_save_choice_from_human_readable_label(self) -> None:
        """
        python manage.py test \
        proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_save_choice_from_human_readable_label
        """

        mock_record = RECORD_1.copy()
        mock_record['Source'] = 'Water'  # 'Water' with capital W is the human-readable value
        mock_sheet_data = [mock_record]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        spc = Sample.objects.get(sample_id=mock_record.get("SampleID"))
        self.assertIsNotNone(spc)
        self.assertEqual(spc.source, 'water', "incorrect value stored")

    def test_eb_put_event(self) -> None:
        """
        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_eb_put_event
        """
        os.environ['EVENT_BUS_NAME'] = TEST_EVENT_BUS_NAME

        mock_dispatch_events = MagicMock()
        libeb.dispatch_events = mock_dispatch_events

        # ####
        # Test if event entries are in the correct format when CREATE new records
        # ####
        metadata_pd = pd.json_normalize([RECORD_1])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        arg = mock_dispatch_events.call_args.args[0]
        expected_created_detail = [
            {
                "action": "CREATE",
                "model": "LIBRARY",
                "refId": "lib.ULID",
                "data": {
                    "libraryId": "L10001",
                }
            }
        ]

        for entry in arg:
            check_put_event_entries_format(self, entry)
            check_put_event_value(self, entry=entry, source="orcabus.metadatamanager",
                                  detail_type="MetadataStateChange",
                                  event_bus_name=TEST_EVENT_BUS_NAME
                                  )
        for event in expected_created_detail:
            self.assertTrue(
                is_expected_event_in_output(self, expected=event, output=[json.loads(i.get('Detail')) for i in arg]))

        # ####
        # Test if record are UPDATE and event entries are correct
        # ####
        updated_record_1 = RECORD_1.copy()
        updated_record_1['Quality'] = 'poor'
        mock_dispatch_events.reset_mock()
        metadata_pd = pd.json_normalize([updated_record_1])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd, SHEET_YEAR)

        arg = mock_dispatch_events.call_args.args[0]
        expected_update_detail = [
            {
                "action": "UPDATE",
                "model": "LIBRARY",
                "refId": "lib.ULID",
                "data": {
                    "libraryId": "L10001",
                }
            },
        ]

        for entry in arg:
            check_put_event_entries_format(self, entry)
            check_put_event_value(self, entry=entry, source="orcabus.metadatamanager",
                                  detail_type="MetadataStateChange",
                                  event_bus_name=TEST_EVENT_BUS_NAME
                                  )
        for event in expected_update_detail:
            self.assertTrue(
                is_expected_event_in_output(self, expected=event, output=[json.loads(i.get('Detail')) for i in arg]))
        # ####
        # Test if the record are DELETE and event entries are correct
        # ####
        mock_dispatch_events.reset_mock()
        empty_pd = metadata_pd.drop(0)  # Remove the only one record data
        persist_lab_metadata(empty_pd, SHEET_YEAR)

        arg = mock_dispatch_events.call_args.args[0]
        expected_delete_detail = [
            {
                "action": "DELETE",
                "model": "LIBRARY",
                "refId": "lib.ULID",
                "data": {
                    "libraryId": "L10001",
                }
            }
        ]

        for entry in arg:
            check_put_event_entries_format(self, entry)
            check_put_event_value(self, entry=entry, source="orcabus.metadatamanager",
                                  detail_type="MetadataStateChange",
                                  event_bus_name=TEST_EVENT_BUS_NAME
                                  )
        for event in expected_delete_detail:
            self.assertTrue(
                is_expected_event_in_output(self, expected=event, output=[json.loads(i.get('Detail')) for i in arg]))
