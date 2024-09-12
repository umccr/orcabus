import os
from unittest.mock import MagicMock
from typing import List

import pandas as pd

from django.test import TestCase
from libumccr.aws import libeb

from app.models import Library, Specimen, Subject

from proc.service.tracking_sheet_srv import sanitize_lab_metadata_df, persist_lab_metadata
from .utils import check_put_event_entries_format, check_put_event_value, is_detail_expected

TEST_EVENT_BUS_NAME = "TEST_BUS"

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
RECORD_3_DIFF_SBJ = {
    **RECORD_3,
    "SubjectID": "SBJ004"
}
RECORD_3_DIFF_SPC = {
    **RECORD_3_DIFF_SBJ,
    "SampleID": "PRJ10004"
}


class TrackingSheetSrvUnitTests(TestCase):

    def setUp(self) -> None:
        super(TrackingSheetSrvUnitTests, self).setUp()
        libeb.dispatch_events = MagicMock()

    def tearDown(self) -> None:
        super(TrackingSheetSrvUnitTests, self).tearDown()

    def test_persist_lab_metadata(self):
        """
        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_persist_lab_metadata
        """
        mock_sheet_data = [RECORD_1, RECORD_2, RECORD_3]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        result = persist_lab_metadata(metadata_pd)

        self.assertEqual(result.get("invalid_record_count"), 0, "non invalid record should exist")

        self.assertEqual(result.get("library").get("new_count"), 3, "3 new library should be created")
        self.assertEqual(result.get("library").get("update_count"), 0, "0 update in library")

        self.assertEqual(result.get("specimen").get("new_count"), 2, "2 new specimen should be created")
        self.assertEqual(result.get("specimen").get("update_count"), 0, "no update in specimen")

        self.assertEqual(result.get("subject").get("new_count"), 1, "1 new subject should be created")
        self.assertEqual(result.get("subject").get("update_count"), 0, "no update in subject")

        lib_1 = Library.objects.get(library_id=RECORD_1.get("LibraryID"))
        self.assertEqual(lib_1.type, RECORD_1.get("Type"), "incorrect value (Type) stored")
        self.assertEqual(lib_1.phenotype, RECORD_1.get("Phenotype"), "incorrect value (Phenotype) stored")
        self.assertEqual(lib_1.assay, RECORD_1.get("Assay"), "incorrect value (Assay) stored")
        self.assertEqual(lib_1.workflow, RECORD_1.get("Workflow"), "incorrect value (Workflow) stored")
        self.assertEqual(lib_1.project_owner, RECORD_1.get("ProjectOwner"), "incorrect value (ProjectOwner) stored")
        self.assertEqual(lib_1.project_name, RECORD_1.get("ProjectName"), "incorrect value (ProjectName) stored")
        self.assertEqual(lib_1.specimen.specimen_id, RECORD_1.get("SampleID"), "incorrect specimen linked")

        spc_1 = Specimen.objects.get(specimen_id=RECORD_1.get("SampleID"))
        self.assertIsNotNone(spc_1)
        self.assertEqual(spc_1.source, RECORD_1.get("Source"), "incorrect value stored")

        sbj_1 = Subject.objects.get(subject_id=RECORD_1.get("SubjectID"))
        self.assertIsNotNone(sbj_1)

        # check relationships if lib_1 and lib_2 is in the same spc_1
        spc_lib_qs = spc_1.library_set.all()
        self.assertEqual(spc_lib_qs.filter(library_id=RECORD_1.get("LibraryID")).count(), 1,
                         "lib_1 and spc_1 is not linked")
        self.assertEqual(spc_lib_qs.filter(library_id=RECORD_2.get("LibraryID")).count(), 1,
                         "lib_2 and spc_1 is not linked")

        # check if all lib is the same with sbj_1
        for rec in mock_sheet_data:
            lib = Library.objects.get(library_id=rec.get("LibraryID"))
            self.assertEqual(lib.specimen.subject.subject_id, RECORD_1.get("SubjectID"),
                             "library is not linked to the same subject")

    def test_persist_lab_metadata_alter_sbj(self):
        """
        test where lib moved to different spc, and spc to different sbj


        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_persist_lab_metadata_alter_sbj
        """

        metadata_pd = pd.json_normalize([RECORD_3])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd)

        metadata_pd = pd.json_normalize([RECORD_3_DIFF_SBJ])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd)

        sbj_4 = Subject.objects.get(subject_id=RECORD_3_DIFF_SBJ['SubjectID'])
        self.assertIsNotNone(sbj_4)
        spc_4 = sbj_4.specimen_set.get(specimen_id=RECORD_3_DIFF_SBJ['SampleID'])
        self.assertEqual(spc_4.specimen_id, RECORD_3_DIFF_SBJ['SampleID'],
                         'specimen obj should not change on link update')

        metadata_pd = pd.json_normalize([RECORD_3_DIFF_SPC])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd)

        lib_3 = Library.objects.get(library_id=RECORD_3['LibraryID'])
        self.assertEqual(lib_3.specimen.specimen_id, RECORD_3_DIFF_SPC['SampleID'],
                         'incorrect link between lib and spc when changing links')

    def test_with_deleted_model(self) -> None:
        """
        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_with_deleted_model
        """
        mock_sheet_data = [RECORD_1, RECORD_2, RECORD_3]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd)

        mock_sheet_data = [RECORD_3]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        result = persist_lab_metadata(metadata_pd)

        deleted_lib = Library.objects.filter(library_id__in=[RECORD_1.get('LibraryID'), RECORD_2.get('LibraryID')])
        self.assertEqual(deleted_lib.count(), 0, 'these library query should all be deleted')
        self.assertEqual(result.get("library").get("delete_count"), 2, "2 library should be deleted")

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
        persist_lab_metadata(metadata_pd)

        spc = Specimen.objects.get(specimen_id=mock_record.get("SampleID"))
        self.assertIsNotNone(spc)
        self.assertEqual(spc.source, 'water', "incorrect value stored")

    def test_eb_put_event(self) -> None:
        """
        python manage.py test proc.tests.test_tracking_sheet_srv.TrackingSheetSrvUnitTests.test_eb_put_event
        """
        os.environ['EVENT_BUS_NAME'] = TEST_EVENT_BUS_NAME

        mock_dispatch_events = MagicMock()
        libeb.dispatch_events = mock_dispatch_events

        """
        Test if event entries are in the correct format when CREATE new records
        """
        metadata_pd = pd.json_normalize([RECORD_1])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd)

        arg = mock_dispatch_events.call_args.args[0]
        expected_created_detail = [
            {
                "action": "CREATE",
                "model": "LIBRARY",
                "ref_id": "lib.ULID",
                "data": {
                    "library_id": "L10001",
                }
            },
            {
                "action": "CREATE",
                "model": "SPECIMEN",
                "ref_id": "spc.ULID",
                "data": {
                    "specimen_id": "PRJ10001",
                }
            },
            {
                "action": "CREATE",
                "model": "SUBJECT",
                "ref_id": "lib.ULID",
                "data": {
                    "subject_id": "SBJ001",
                }
            }
        ]

        for entry in arg:
            check_put_event_entries_format(self, entry)
            check_put_event_value(self, entry=entry, source="orcabus.metadatamanager",
                                  detail_type="MetadataStateChange",
                                  event_bus_name=TEST_EVENT_BUS_NAME
                                  )
            self.assertTrue(is_detail_expected(self, detail=entry.get('Detail'), expected_list=expected_created_detail))

        """
        Test if record are UPDATE and event entries are correct
        """
        updated_record_1 = RECORD_1.copy()
        updated_record_1['Quality'] = 'poor'
        mock_dispatch_events.reset_mock()
        metadata_pd = pd.json_normalize([updated_record_1])
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        persist_lab_metadata(metadata_pd)

        arg = mock_dispatch_events.call_args.args[0]
        expected_update_detail = [
            {
                "action": "UPDATE",
                "model": "LIBRARY",
                "ref_id": "lib.ULID",
                "data": {
                    "library_id": "L10001",
                }
            },
        ]

        for entry in arg:
            check_put_event_entries_format(self, entry)
            check_put_event_value(self, entry=entry, source="orcabus.metadatamanager",
                                  detail_type="MetadataStateChange",
                                  event_bus_name=TEST_EVENT_BUS_NAME
                                  )
            self.assertTrue(is_detail_expected(self, detail=entry.get('Detail'), expected_list=expected_update_detail))

        """
        Test if the record are DELETE and event entries are correct
        """
        mock_dispatch_events.reset_mock()
        empty_pd = metadata_pd.drop(0)  # Remove the only one record data
        persist_lab_metadata(empty_pd)

        arg = mock_dispatch_events.call_args.args[0]
        expected_delete_detail = [
            {
                "action": "DELETE",
                "model": "LIBRARY",
                "ref_id": "lib.ULID",
                "data": {
                    "library_id": "L10001",
                }
            },
            {
                "action": "DELETE",
                "model": "SPECIMEN",
                "ref_id": "spc.ULID",
                "data": {
                    "specimen_id": "PRJ10001",
                }
            },
            {
                "action": "DELETE",
                "model": "SUBJECT",
                "ref_id": "lib.ULID",
                "data": {
                    "subject_id": "SBJ001",
                }
            }
        ]
        for entry in arg:
            check_put_event_entries_format(self, entry)
            check_put_event_value(self, entry=entry, source="orcabus.metadatamanager",
                                  detail_type="MetadataStateChange",
                                  event_bus_name=TEST_EVENT_BUS_NAME
                                  )
            self.assertTrue(is_detail_expected(self, detail=entry.get('Detail'), expected_list=expected_delete_detail))

