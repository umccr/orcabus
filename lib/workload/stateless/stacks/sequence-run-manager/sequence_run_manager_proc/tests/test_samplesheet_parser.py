import json
from pathlib import Path

from unittest import TestCase
from sequence_run_manager_proc.services.v2_samplesheet_parser.parser import parse_samplesheet

class TestSampleSheetParser(TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def tearDown(self):
        super().tearDown()

    def test_parse_standard_sheet_with_settings(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_samplesheet_parser.TestSampleSheetParser.test_parse_standard_sheet_with_settings
        """
        
        # read files from ./examples/standard-sheet-with-settings.csv
        with open(Path(__file__).parent / "examples/standard-sheet-with-settings.csv", "r") as f:
            samplesheet = f.read()
        result = parse_samplesheet(samplesheet)
        # read expected result from ./examples/standard-sheet-with-settings.json
        with open(Path(__file__).parent / "examples/standard-sheet-with-settings.json", "r") as f:
            expected_result = json.load(f)
        self.compare_dicts(result, expected_result)
        self.assertEqual(result, expected_result)

    def test_parse_tso500_cloud_settings(self):
        """
        python manage.py test sequence_run_manager_proc.tests.test_samplesheet_parser.TestSampleSheetParser.test_parse_tso500_cloud_settings
        """
        # read files from ./examples/tso500-cloud-settings.csv
        with open(Path(__file__).parent / "examples/tso500-cloud-settings.csv", "r") as f:
            samplesheet = f.read()
        result = parse_samplesheet(samplesheet)
        # read expected result from ./examples/tso500-cloud-settings.json
        with open(Path(__file__).parent / "examples/tso500-cloud-settings.json", "r") as f:
            expected_result = json.load(f)
        self.compare_dicts(result, expected_result)
        self.assertEqual(result, expected_result)
        
    def compare_dicts(self, actual: dict, expected: dict, path: str = ""):
        """Compare dictionaries and print differences"""
        for key in set(actual.keys()) | set(expected.keys()):
            current_path = f"{path}.{key}" if path else key
            if key not in actual:
                print(f"Missing key in actual: {current_path}")
            elif key not in expected:
                print(f"Extra key in actual: {current_path}")
            elif actual[key] != expected[key]:
                print(f"Value mismatch at {current_path}:")
                print(f"  Actual: {actual[key]}")
                print(f"  Expected: {expected[key]}")