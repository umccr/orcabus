import httpx
import pytest
from os import environ
import logging

# Set up basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8457"

CREATE_DATA_PAYLOAD = {
  "rgid": "CTTGTCGA+CGATGTTC.23",
  "index": "CTTGTCGA",
  "index2": "CGATGTTC",
  "lane": 1,
  "instrument_run_id": "240424_A01052_0193_BH7JMMDRX5",
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
        "s3IngestId": "0193cdc0-4c7a-7e23-8d4d-00561ae2ca59"
    }
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
            response = await client.post("http://localhost:8457/api/v1/fastq/", json=CREATE_DATA_PAYLOAD)
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
        response = await client.post("http://localhost:8457/api/v1/fastq/", json=CREATE_DATA_PAYLOAD)
        response_data = response.json()
        fastq_list_row_data = FastqListRowData(**response_data)
        assert isinstance(fastq_list_row_data, FastqListRowData)

        # Add file
        logger.info("Adding file to object we just created")
        file_response = await client.patch(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}/addFastqPairStorageObject", json=FILE_PAYLOAD)

        # Assert we have a 200 file_response
        assert file_response.status_code == 200

        # Now delete the entry we just created
        logger.info("Deleting object on endpoint we just created")
        delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")

        # Assert we have a 200 delete_response
        assert delete_response.status_code == 200

