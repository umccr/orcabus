import httpx
import pytest
from os import environ
import logging

# Set up basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8457"

CREATE_DATA_PAYLOAD = {
  "rgid": "CTTGTCGA+CGATGTTC.1",
  "index": "CTTGTCGA",
  "index2": "CGATGTTC",
  "lane": 1,
  "instrument_run_id": "240424_A01052_0193_BH7JMMDRX4",
  "isValid": True,
  "library": {
      "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
      "libraryId": "LPRJ240775"
  }
}

FILE_PAYLOAD = {
    "r1": {
        "s3IngestId": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
    },
    "r2": {
        "s3IngestId": "0193cdc0-4c7a-7e23-8d4d-00561ae2ca59",
        "rawMd5sum": "d41d8cd98f00b204e9800998ecf8427e"  # pragma: allowlist secret
    }
}

FILE_COMPRESSION_INFO = {
    "compressionFormat": "ORA",
    "r1GzipCompressionSizeInBytes": 100,
    "r2GzipCompressionSizeInBytes": 100
}

QC_INFO = {
    "insertSizeEstimate": 100,
    "rawWgsCoverageEstimate": 100,
    "r1Q20Fraction": 0.9,
    "r2Q20Fraction": 0.9,
    "r1GcFraction": 0.5,
    "r2GcFraction": 0.5,
}

@pytest.fixture(scope="module", autouse=True)
def setup_env():
    environ["DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME"] = "fastq_list_row"
    environ["DYNAMODB_HOST"] = "http://localhost:8456"


@pytest.mark.asyncio
async def test_post_endpoint():
    from fastq_manager_api_tools.models.fastq_list_row import FastqListRowData
    async with httpx.AsyncClient() as client:
        try:
            logger.info("Creating object on endpoint")
            response = await client.post("http://localhost:8457/api/v1/fastq", json=CREATE_DATA_PAYLOAD)
            response_data = response.json()
            fastq_list_row_data = FastqListRowData(**response_data)
            assert isinstance(fastq_list_row_data, FastqListRowData)
        finally:
            if 'fastq_list_row_data' in locals():
                logger.info("Deleting object on endpoint we just created")
                delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")
                # Assert we have a 200 delete_response
                assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_add_files_endpoint():
    from fastq_manager_api_tools.models.fastq_list_row import FastqListRowData
    async with httpx.AsyncClient() as client:
        logger.info("Creating object on endpoint")
        try:
            response = await client.post("http://localhost:8457/api/v1/fastq", json=CREATE_DATA_PAYLOAD)
            response_data = response.json()
            fastq_list_row_data = FastqListRowData(**response_data)
            assert isinstance(fastq_list_row_data, FastqListRowData)

            # Add file
            logger.info("Adding file to object we just created")
            file_response = await client.patch(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}/addFastqPairStorageObject", json=FILE_PAYLOAD)

            # Assert we have a 200 file_response
            assert file_response.status_code == 200

            # Assert that the raw md5sum exists
            assert file_response.json()['readSet']['r2']['rawMd5sum'] == FILE_PAYLOAD['r2']['rawMd5sum']

        finally:
            if 'fastq_list_row_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")

                # Assert we have a 200 delete_response
                assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_add_file_compression_information_endpoint():
    from fastq_manager_api_tools.models.fastq_list_row import FastqListRowData
    async with httpx.AsyncClient() as client:
        logger.info("Creating object on endpoint")
        try:
            response = await client.post("http://localhost:8457/api/v1/fastq", json=CREATE_DATA_PAYLOAD)
            response_data = response.json()
            fastq_list_row_data = FastqListRowData(**response_data)
            assert isinstance(fastq_list_row_data, FastqListRowData)

            # Add file
            logger.info("Adding file to object we just created")
            file_response = await client.patch(
                f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}/addFastqPairStorageObject",
                json=FILE_PAYLOAD
            )

            # Add file compression info
            logger.info("Adding file compression info to object we just created")
            file_compression_response = await client.patch(
                f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}/addFileCompressionInformation",
                json=FILE_COMPRESSION_INFO
            )

            # Assert we have a 200 file_response
            assert file_compression_response.status_code == 200

            # Get fastq and assert compression info is there
            logger.info("Getting object on endpoint")
            get_response = await client.get(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")
            get_response_data = get_response.json()

            # Assert we have a 200 get_response
            assert get_response.status_code == 200

            # Assert we have the correct compression info
            assert get_response_data['readSet']['compressionFormat'] == FILE_COMPRESSION_INFO['compressionFormat']
            assert get_response_data['readSet']['r1']['gzipCompressionSizeInBytes'] == FILE_COMPRESSION_INFO['r1GzipCompressionSizeInBytes']

        finally:
            if 'fastq_list_row_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")

                # Assert we have a 200 delete_response
                assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_add_qc_info_endpoint():
    from fastq_manager_api_tools.models.fastq_list_row import FastqListRowData
    async with httpx.AsyncClient() as client:
        logger.info("Creating object on endpoint")
        try:
            response = await client.post("http://localhost:8457/api/v1/fastq", json=CREATE_DATA_PAYLOAD)
            response_data = response.json()
            fastq_list_row_data = FastqListRowData(**response_data)
            assert isinstance(fastq_list_row_data, FastqListRowData)

            # Add qc info
            # Add file compression info
            logger.info("Adding file compression info to object we just created")
            qc_response = await client.patch(
                f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}/addQcStats",
                json=QC_INFO
            )

            # Assert we have a 200 file_response
            assert qc_response.status_code == 200
        finally:
            if 'fastq_list_row_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")

                # Assert we have a 200 delete_response
                assert delete_response.status_code == 200