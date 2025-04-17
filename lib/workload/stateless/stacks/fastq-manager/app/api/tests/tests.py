import httpx
import pytest
from os import environ
import logging

# Set up basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8457"

CREATE_DATA_PAYLOAD = {
    "index": "CTTGTCGA+CGATGTTC",
    "lane": 1,
    "instrument_run_id": "240424_A01052_0193_BH7JMMDRX4",
    "isValid": True,
    "library": {
        "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
        "libraryId": "LPRJ240775"
    }
}

CREATE_DATA_PAYLOAD_2 = {
    "index": "CTTGTCGA+CGATGTTC",
    "lane": 2,
    "instrument_run_id": "240424_A01052_0193_BH7JMMDRX4",
    "isValid": True,
    "library": {
        "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
        "libraryId": "LPRJ240775"
    }
}

FILE_PAYLOAD = {
    "r1": {
        "ingestId": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
    },
    "r2": {
        "ingestId": "0193cdc0-4c7a-7e23-8d4d-00561ae2ca59",
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

CREATE_SET_PAYLOAD = {
    "library": {
        "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
        "libraryId": "LPRJ240775"
    },
    "fastqSet": [
        CREATE_DATA_PAYLOAD,
        CREATE_DATA_PAYLOAD_2
    ]
}

CREATE_SET_PAYLOAD_1_ONLY = {
    "library": {
        "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
        "libraryId": "LPRJ240775"
    },
    "fastqSet": [
        CREATE_DATA_PAYLOAD
    ]
}

CREATE_SET_PAYLOAD_2_ONLY = {
    "library": {
        "orcabusId": "lib.01J9T97T3CZKPB51BQ5PCT968R",
        "libraryId": "LPRJ240775"
    },
    "fastqSet": [
        CREATE_DATA_PAYLOAD_2
    ]
}


@pytest.fixture(scope="module", autouse=True)
def setup_env():
    DYNAMODB_PORT = 8456
    FASTQ_MANAGER_API_PORT = 8457
    environ["DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME"] = "fastq_list_row"
    environ["DYNAMODB_FASTQ_SET_TABLE_NAME"] = "fastq_set"
    environ["DYNAMODB_HOST"] = f"http://localhost:{DYNAMODB_PORT}"
    environ["AWS_REGION"] = "us-east-1"
    environ["EVENT_DETAIL_TYPE_CREATE_FASTQ_LIST_ROW"] = "FastqListRowCreate"
    environ["EVENT_DETAIL_TYPE_UPDATE_FASTQ_LIST_ROW"] = "FastqListRowUpdate"
    environ["EVENT_DETAIL_TYPE_DELETE_FASTQ_LIST_ROW"] = "FastqListRowDelete"
    environ["EVENT_DETAIL_TYPE_CREATE_FASTQ_SET"] = "FastqSetCreate"
    environ["EVENT_DETAIL_TYPE_UPDATE_FASTQ_SET"] = "FastqSetUpdate"
    environ["EVENT_DETAIL_TYPE_MERGE_FASTQ_SET"] = "FastqSetMerge"
    environ["EVENT_DETAIL_TYPE_DELETE_FASTQ_SET"] = "FastqSetDelete"
    environ["FASTQ_BASE_URL"] = f"http://localhost:{FASTQ_MANAGER_API_PORT}"


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
async def test_query_by_library_id_endpoint():
    from fastq_manager_api_tools.models.fastq_list_row import FastqListRowData
    async with httpx.AsyncClient() as client:
        try:
            logger.info("Creating object on endpoint")
            response = await client.post("http://localhost:8457/api/v1/fastq", json=CREATE_DATA_PAYLOAD)
            response_data = response.json()
            fastq_list_row_data = FastqListRowData(**response_data)
            assert isinstance(fastq_list_row_data, FastqListRowData)

            logger.info("Query object on endpoint")
            query_response = await client.get(
                "http://localhost:8457/api/v1/fastq",
                params={
                    "library[]": [
                        CREATE_DATA_PAYLOAD['library']['orcabusId']
                    ]
                }
            )
            response_data = query_response.json()
            assert len(response_data) == 3
            fastq_list_row_data = FastqListRowData(**response_data['results'][0])
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
            file_response = await client.patch(
                f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}/addFastqPairStorageObject",
                json=FILE_PAYLOAD)

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
            assert get_response_data['readSet']['r1']['gzipCompressionSizeInBytes'] == FILE_COMPRESSION_INFO[
                'r1GzipCompressionSizeInBytes']

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


@pytest.mark.asyncio
async def test_add_fastq_set_endpoint():
    from fastq_manager_api_tools.models.fastq_set import FastqSetData
    async with httpx.AsyncClient() as client:
        logger.info("Creating object on endpoint")
        try:
            response = await client.post("http://localhost:8457/api/v1/fastqSet", json=CREATE_SET_PAYLOAD)
            response_data = response.json()
            fastq_set_data = FastqSetData.from_response(**response_data)
            assert isinstance(fastq_set_data, FastqSetData)

            # Add file
            logger.info("Adding file to object we just created")
            file_response = await client.patch(
                f"http://localhost:8457/api/v1/fastq/{fastq_set_data.fastq_set_ids[0]}/addFastqPairStorageObject",
                json=FILE_PAYLOAD
            )

            # Assert we have a 200 file_response
            assert file_response.status_code == 200

            # Re get the fastq set
            response = await client.get(f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}")
            response_data = response.json()

            # Assert that the raw md5sum exists
            assert file_response.json()['readSet']['r2']['rawMd5sum'] == FILE_PAYLOAD['r2']['rawMd5sum']

            # Assert that the raw md5sum can be found in the re-get
            assert response_data['fastqSet'][0]['readSet']['r2']['rawMd5sum'] == FILE_PAYLOAD['r2']['rawMd5sum']

        finally:
            if 'fastq_set_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                for fastq_list_row_id in fastq_set_data.fastq_set_ids:
                    unlink_response = await client.patch(
                        f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}/unlinkFastq/{fastq_list_row_id}")
                    delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_id}")

                    # Assert we have a 200 delete_response
                    assert delete_response.status_code == 200

                # Assert a get request returns a 404
                # Since unlinking the fastq list row from the fastq set should delete the fastq set
                response = await client.get(f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}")
                assert response.status_code == 404


# Test linking of fastq
@pytest.mark.asyncio
async def test_link_fastq_set_endpoint():
    from fastq_manager_api_tools.models.fastq_set import FastqSetData
    from fastq_manager_api_tools.models.fastq_list_row import FastqListRowData
    async with httpx.AsyncClient() as client:
        logger.info("Creating object on endpoint")
        try:
            response = await client.post("http://localhost:8457/api/v1/fastqSet", json=CREATE_SET_PAYLOAD_1_ONLY)
            response_data = response.json()
            fastq_set_data = FastqSetData.from_response(**response_data)
            assert isinstance(fastq_set_data, FastqSetData)

            # Add fastq
            logger.info("Create an independent fastq object")
            response = await client.post("http://localhost:8457/api/v1/fastq", json=CREATE_DATA_PAYLOAD_2)
            response_data = response.json()
            fastq_list_row_data = FastqListRowData(**response_data)
            assert isinstance(fastq_list_row_data, FastqListRowData)

            # Open up for 'allow additional fastqs'
            file_response = await client.patch(
                f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}/allowAdditionalFastqs"
            )

            # Assert we have a 200 file_response
            assert file_response.status_code == 200

            file_response = await client.patch(
                f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}/linkFastq/{fastq_list_row_data.id}"
            )

            # Assert we have a 200 file_response
            assert file_response.status_code == 200

            # Assert length of fastq set is 2
            response = await client.get(f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}")
            fastq_set_response = response.json()
            fastq_set_data = FastqSetData.from_response(**fastq_set_response)

            assert len(fastq_set_data.fastq_set_ids) == 2


        finally:
            if 'fastq_set_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                for fastq_list_row_id in fastq_set_data.fastq_set_ids:
                    unlink_response = await client.patch(
                        f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}/unlinkFastq/{fastq_list_row_id}")
                    delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_id}")

                # Assert we have a 200 delete_response
                assert delete_response.status_code == 200

            if 'fastq_list_row_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")

                # Assert we have a 200 delete_response
                # This data may have already been deleted
                # assert delete_response.status_code == 200


# Test unlinking of fastq
@pytest.mark.asyncio
async def test_unlink_fastq_set_endpoint():
    from fastq_manager_api_tools.models.fastq_set import FastqSetData
    from fastq_manager_api_tools.models.fastq_list_row import FastqListRowData
    async with httpx.AsyncClient() as client:
        logger.info("Creating object on endpoint")
        try:
            response = await client.post("http://localhost:8457/api/v1/fastqSet", json=CREATE_SET_PAYLOAD_1_ONLY)
            response_data = response.json()
            fastq_set_data = FastqSetData.from_response(**response_data)
            assert isinstance(fastq_set_data, FastqSetData)

            # Unlink the fastq set
            file_response = await client.patch(
                f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}/unlinkFastq/{fastq_set_data.fastq_set_ids[0]}"
            )

            # Confirm that the fastq list row is no longer linked to any fastq sets
            response = await client.get(f"http://localhost:8457/api/v1/fastq/{fastq_set_data.fastq_set_ids[0]}")
            fastq_list_row_data = FastqListRowData(**response.json())

            # Assert we have a 200 file_response
            assert response.status_code == 200

            # Assert that the fastq list row is no longer linked to any fastq sets
            assert fastq_list_row_data.fastq_set_id is None

        finally:
            if 'fastq_list_row_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_data.id}")

                # Assert we have a 200 delete_response
                # This data may have already been deleted
                # assert delete_response.status_code == 200


# Test merge of fastqs
@pytest.mark.asyncio
async def test_merge_fastq_set_endpoint():
    from fastq_manager_api_tools.models.fastq_set import FastqSetData
    async with httpx.AsyncClient() as client:
        logger.info("Creating object on endpoint")
        try:
            response = await client.post("http://localhost:8457/api/v1/fastqSet", json=CREATE_SET_PAYLOAD_1_ONLY)
            response_data = response.json()
            assert response.status_code == 200

            fastq_set_data_1 = FastqSetData.from_response(**response_data)
            assert isinstance(fastq_set_data_1, FastqSetData)

            fastq_set_2_post_payload = CREATE_SET_PAYLOAD_2_ONLY.copy()

            fastq_set_2_post_payload['isCurrentFastqSet'] = False

            response = await client.post("http://localhost:8457/api/v1/fastqSet", json=fastq_set_2_post_payload)
            response_data = response.json()
            print(response.text)
            assert response.status_code == 200

            fastq_set_data_2 = FastqSetData.from_response(**response_data)
            assert isinstance(fastq_set_data_2, FastqSetData)

            # Merge the fastq sets
            response = await client.patch(
                f"http://localhost:8457/api/v1/fastqSet/merge",
                json=[
                    fastq_set_data_1.id,
                    fastq_set_data_2.id
                ]
            )

            # Assert we have a 200 response
            assert response.status_code == 200

            # Get fastq set data
            fastq_set_data = FastqSetData.from_response(**response.json())

            # Assert that the fastq set has been merged
            assert len(fastq_set_data.fastq_set_ids) == (
                        len(fastq_set_data_1.fastq_set_ids) + len(fastq_set_data_2.fastq_set_ids))

            # Assert that the id is different
            assert fastq_set_data.id != fastq_set_data_1.id
            assert fastq_set_data.id != fastq_set_data_2.id

        finally:
            if 'fastq_set_data' in locals():
                # Now delete the entry we just created
                logger.info("Deleting object on endpoint we just created")
                for fastq_list_row_id in fastq_set_data.fastq_set_ids:
                    unlink_response = await client.patch(
                        f"http://localhost:8457/api/v1/fastqSet/{fastq_set_data.id}/unlinkFastq/{fastq_list_row_id}")
                    delete_response = await client.delete(f"http://localhost:8457/api/v1/fastq/{fastq_list_row_id}")
