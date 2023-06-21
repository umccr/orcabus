import tempfile
from unittest import skip
from datetime import datetime, timezone

import logging
import pandas as pd
from libumccr import libgdrive, libjson
from libumccr.aws import libssm
from mockito import when

from metadata_manager.models.metadata import Metadata
from metadata_manager_proc.lambdas import metadata_proc
from metadata_manager_proc.tests.case import MetadataProcUnitTestCase

logger = logging.getLogger()
logger.setLevel(logging.INFO)

labmetadata_csv_columns = [
    "LibraryID",
    "SampleName",
    "SampleID",
    "ExternalSampleID",
    "SubjectID",
    "ExternalSubjectID",
    "Phenotype",
    "Quality",
    "Source",
    "ProjectName",
    "ProjectOwner",
    "",
    "ExperimentID",
    "Type",
    "Assay",
    "OverrideCycles",
    "Workflow",
    "Coverage (X)",
    "TruSeq Index, unless stated",
    "Run#",
    "Comments",
    "rRNA",
    "qPCR ID",
    "Sample_ID (SampleSheet)",
]

_mock_labmetadata_sheet_content = b"""
LibraryID,SampleName,SampleID,ExternalSampleID,SubjectID,ExternalSubjectID,Phenotype,Quality,Source,ProjectName,ProjectOwner,,ExperimentID,Type,Assay,OverrideCycles,Workflow,Coverage (X),"TruSeq Index, unless stated",Run#,Comments,rRNA,qPCR ID,Sample_ID (SampleSheet),,,,,,,,,,
LIB01,SAMIDA-EXTSAMA,SAMIDA,,SUBIDA,EXTSUBIDA,,,FFPE,MyPath,Alice,,Exper1,WTS,NebRNA,Y151;I8;I8;Y151,clinical,6.0,Neb2-F07,P30,,,#NAME?,SAMIDA_LIB01,,,,,,,,,,
LIB02,SAMIDB-EXTSAMB,SAMIDB,EXTSAMB,SUBIDB,EXTSUBIDB,tumor,poor,FFPE,Fake,Bob,,Exper1,WTS,NebRNA,Y151;I8;I8;Y151,clinical,6.0,Neb2-G07,P30,,,#NAME?,SAMIDB_LIB02,,,,,,,,,,
LIB03,SAMIDB-EXTSAMB,SAMIDB,EXTSAMB,SUBIDB,EXTSUBIDB,tumor,poor,FFPE,Fake,Bob,,Exper1,WTS,NebRNA,Y151;I8;I8;Y151,clinical,6.0,Neb2-H07,P30,,,#NAME?,SAMIDB_LIB03,,,,,,,,,,
LIB04,SAMIDA-EXTSAMA,SAMIDA,EXTSAMA,SUBIDA,EXTSUBIDA,tumor,poor,FFPE,MyPath,Alice,,Exper1,WTS,NebRNA,Y151;I8;I8;Y151,clinical,6.0,Neb2-F07,P30,,,#NAME?,SAMIDA_LIB01,,,,,,,,,,
"""


class MetadataProcUnitTests(MetadataProcUnitTestCase):
    def test_metadata_append(self):
        """
        python manage.py test metadata_manager_proc.tests.test_metadata_proc.MetadataProcUnitTests.test_metadata_append
        """
        logger.info("Test sync metadata with existing database\n")

        mock_labmetadata_sheet = tempfile.NamedTemporaryFile(suffix=".csv", delete=True)
        mock_labmetadata_sheet.write(_mock_labmetadata_sheet_content.lstrip().rstrip())
        mock_labmetadata_sheet.seek(0)
        mock_labmetadata_sheet.flush()

        # print csv file in tmp dir -- if delete=False, you can see the mock csv content
        logger.info(f"Path to mock tracking sheet: {mock_labmetadata_sheet.name}")
        when(libssm).get_secret(...).thenReturn("SomeSecretString")
        when(libgdrive).download_sheet(...).thenReturn(
            pd.read_csv(mock_labmetadata_sheet)
        )

        # make a duplicate to test update, its phenotype is normal but in sheet it is tumor
        metadata = Metadata(
            library_id="LIB03",
            sample_name="SAMIDB-EXTSAMB",
            sample_id="SAMIDB",
            external_sample_id="EXTSAMB",
            subject_id="SUBIDB",
            external_subject_id="EXTSUBIDB",
            phenotype="NORMAL",
            quality="poor",
            source="FFPE",
            project_name="Fake",
            project_owner="Bob",
            experiment_id="Exper1",
            type="WTS",
            assay="NebRNA",
            override_cycles="Y151;I8;I8;Y151",
            workflow="clinical",
            coverage="6.0",
            truseqindex="H07",
            timestamp=datetime.now(tz=timezone.utc),
        )
        metadata.save()

        mock_sheet_year = "2021"
        result = metadata_proc.sync_metadata_from_gdrive(
            {
                "sheets": [mock_sheet_year],
            },
            None,
        )

        logger.info("Example labmetadata.scheduled_update_handler lambda output:")
        logger.info(libjson.dumps(result))

        self.assertEqual(result[mock_sheet_year]["metadata_row_created_count"], 4)
        self.assertEqual(result[mock_sheet_year]["metadata_row_invalid_count"], 0)

        lib_blank_ext_sample_id = Metadata.objects.get_single(library_id="LIB01")
        self.assertEqual(lib_blank_ext_sample_id.external_sample_id, "")

        lib_created = Metadata.objects.get_single(library_id="LIB02")
        self.assertIsNotNone(lib_created)

        # Check if lib is successfully updated
        lib_updated = Metadata.objects.get_single(library_id="LIB03")
        self.assertEqual(lib_updated.phenotype, "tumor")

        # Check if both record exist for the updated library
        lib_updated_history = Metadata.objects.get_by_keyword(
            library_id="LIB03", show_history=True
        )
        self.assertEqual(
            len(lib_updated_history), 2, "updated records should now have history"
        )

        # Check newly inserted timestamp are the same
        lib_01 = Metadata.objects.get_single(library_id="LIB01")
        lib_02 = Metadata.objects.get_single(library_id="LIB02")
        self.assertEqual(
            lib_01.timestamp,
            lib_02.timestamp,
            "newly inserted record must have the same timestamp",
        )

        # clean up
        mock_labmetadata_sheet.close()

    def test_sync_idempotent(self):
        """
        Not inserting new record if existing record has exist

        python manage.py test metadata_manager_proc.tests.test_metadata_proc.MetadataProcUnitTests.test_sync_idempotent
        """
        logger.info(
            "Test sync metadata is idempotent (without replacing existing one)\n"
        )

        mock_sheet_year = "2021"
        mock_labmetadata_sheet = tempfile.NamedTemporaryFile(suffix=".csv", delete=True)
        mock_labmetadata_sheet.write(_mock_labmetadata_sheet_content.lstrip().rstrip())
        mock_labmetadata_sheet.seek(0)
        mock_labmetadata_sheet.flush()

        when(libssm).get_secret(...).thenReturn("SomeSecretString")
        when(libgdrive).download_sheet(...).thenReturn(
            pd.read_csv(mock_labmetadata_sheet)
        )

        # Inserting metadata into a black db
        first_sync = metadata_proc.sync_metadata_from_gdrive(
            {
                "sheets": [mock_sheet_year],
            },
            None,
        )
        self.assertEqual(
            first_sync[mock_sheet_year]["metadata_row_created_count"],
            4,
            "expecting to insert all records",
        )

        # Test if sync from same metadata will result in no new records
        second_sync = metadata_proc.sync_metadata_from_gdrive(
            {
                "sheets": [mock_sheet_year],
            },
            None,
        )
        self.assertEqual(
            second_sync[mock_sheet_year]["metadata_row_created_count"],
            0,
            "expecting no record as it is based from previous metadata",
        )
