import pandas as pd
from django.core.management import BaseCommand

from proc.service.tracking_sheet_srv import sanitize_lab_metadata_df, persist_lab_metadata
from proc.tests.test_tracking_sheet_srv import RECORD_1, RECORD_2, RECORD_3


class Command(BaseCommand):
    help = "Generate mock Metadata into database for local development and testing"

    def handle(self, *args, **options):
        print("insert data from proc service test")

        mock_sheet_data = [RECORD_1, RECORD_2, RECORD_3]

        metadata_pd = pd.json_normalize(mock_sheet_data)
        metadata_pd = sanitize_lab_metadata_df(metadata_pd)
        result = persist_lab_metadata(metadata_pd)

        print("insert mock data completed")
