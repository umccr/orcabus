"""
Unit tests for samplesheet checker

run: python -m unittest samplesheet/tests/test_samplesheet_check.py

"""

import logging
import os

from unittest import TestCase, mock, main

from src.checker import run_sample_sheet_check_with_metadata, run_sample_sheet_content_check
from src.samplesheet import SampleSheet
from src.errors import SampleNameFormatError
from src.errors import GetMetaDataError, SampleSheetHeaderError, SimilarIndexError, \
    MetaDataError, OverrideCyclesError

dirname = os.path.dirname(__file__)
SAMPLE1_PATH = os.path.join(dirname, "./sample/mock-1.csv")
SAMPLE2_PATH = os.path.join(dirname, "./sample/mock-2.csv")


class TestSamplesheetCheckUnitTestCase(TestCase):
    sample_sheet = None

    @classmethod
    def setUpClass(cls) -> None:
        logging.disable(logging.CRITICAL)
        print("\n---Running sample sheet check unit tests---")

    def test_fail_sample_name_check(self):
        with self.assertRaises(SampleNameFormatError):
            SampleSheet(SAMPLE1_PATH)

    def test_success_sample_format(self):
        sample_sheet = SampleSheet(SAMPLE2_PATH)
        try:
            run_sample_sheet_content_check(sample_sheet)
        except Exception as e:
            self.fail("Should not raise an exception", e)

    @mock.patch('src.checker.check_sample_sheet_for_index_clashes', mock.MagicMock(
        side_effect=SimilarIndexError("Found at least two indexes that were too similar to each other")))
    def test_run_check_SimilarIndexError(self):
        ss = SampleSheet(SAMPLE2_PATH)
        with self.assertRaises(SimilarIndexError) as context:
            run_sample_sheet_content_check(ss)
        self.assertEqual(str(context.exception), "Found at least two indexes that were too similar to each other",
                         "Expected error")

    @mock.patch('src.checker.check_samplesheet_header_metadata',
                mock.MagicMock(
                    side_effect=SampleSheetHeaderError("Samplesheet header did not have the appropriate attributes")))
    def test_run_check_SampleSheetHeaderError(self):
        ss = SampleSheet(SAMPLE2_PATH)
        with self.assertRaises(SampleSheetHeaderError) as context:
            run_sample_sheet_content_check(ss)
        self.assertEqual(str(context.exception), "Samplesheet header did not have the appropriate attributes")

    @mock.patch.object(SampleSheet, 'set_metadata_from_api',
                       mock.MagicMock(side_effect=GetMetaDataError("Unable to get metadata")))
    def test_run_check_GetMetaDataError(self):
        ss = SampleSheet(SAMPLE2_PATH)
        with self.assertRaises(GetMetaDataError) as context:
            run_sample_sheet_check_with_metadata(ss, "MOCK_JWT")
        self.assertEqual(str(context.exception), "Unable to get metadata")

    @mock.patch('src.checker.check_metadata_correspondence',
                mock.MagicMock(side_effect=MetaDataError("Metadata could not be extracted")))
    @mock.patch.object(SampleSheet, 'set_metadata_from_api', mock.MagicMock(return_value=None))
    def test_run_check_MetaDataError(self):

        ss = SampleSheet(SAMPLE2_PATH)
        with self.assertRaises(MetaDataError) as context:
            run_sample_sheet_check_with_metadata(ss, "MOCK_JWT")
        self.assertEqual(str(context.exception), "Metadata could not be extracted")

    @mock.patch('src.checker.check_global_override_cycles',
                mock.MagicMock(side_effect=OverrideCyclesError("Override cycles check failed")))
    @mock.patch.object(SampleSheet, 'set_metadata_from_api', mock.MagicMock(return_value=None))
    @mock.patch('src.checker.check_metadata_correspondence',
                mock.MagicMock(return_value=mock.MagicMock(return_value=None)))
    def test_run_check_globalOverrideCyclesError(self):

        ss = SampleSheet(SAMPLE2_PATH)
        with self.assertRaises(OverrideCyclesError) as context:
            run_sample_sheet_check_with_metadata(ss, "MOCK_JWT")
        self.assertEqual(str(context.exception), "Override cycles check failed")

    @mock.patch('src.checker.check_internal_override_cycles',
                mock.MagicMock(side_effect=OverrideCyclesError("Override cycles check failed")))
    @mock.patch.object(SampleSheet, 'set_metadata_from_api', mock.MagicMock(return_value=None))
    @mock.patch('src.checker.check_metadata_correspondence',
                mock.MagicMock(return_value=mock.MagicMock(return_value=None)))
    @mock.patch('src.checker.check_global_override_cycles',
                mock.MagicMock(return_value=mock.MagicMock(return_value=None)))
    def test_run_check_internalOverrideCyclesError(self):

        ss = SampleSheet(SAMPLE2_PATH)
        with self.assertRaises(OverrideCyclesError) as context:
            run_sample_sheet_check_with_metadata(ss, "MOCK_JWT")
        self.assertEqual(str(context.exception), "Override cycles check failed")
