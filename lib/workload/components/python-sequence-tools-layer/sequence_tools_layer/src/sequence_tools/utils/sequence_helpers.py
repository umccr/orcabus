#!/usr/bin/env python3


from .models import Sequence, SequenceDetail, SampleSheet
from .requests_helpers import get_request_response_results, get_request_response


def get_sequence_object_from_instrument_run_id(instrument_run_id: str) -> SequenceDetail:
    """
    Get the sequence object from the instrument run id.
    :param instrument_run_id:
    :return:
    """

    return Sequence(
        **dict(
            get_request_response_results(
                endpoint="api/v1/sequence",
                params={
                    "instrumentRunId": instrument_run_id,
                }
            )[0]
        )
    )


def get_sample_sheet_from_orcabus_id(sequence_orcabus_id: str) -> SampleSheet:
    """
    Get the sample sheet from the orcabus id.
    :param sequence_orcabus_id:
    :return:
    """

    return SampleSheet(
        **dict(
            get_request_response(
                endpoint=f"api/v1/sequence/{sequence_orcabus_id}/sample_sheet"
            )
        )
    )


def get_library_ids_in_sequence(sequence_orcabus_id: str) -> list[str]:
    """
    Get the library ids in the sequence run.
    :param sequence_orcabus_id:
    :return:
    """

    return get_request_response(
        endpoint=f"api/v1/sequence/{sequence_orcabus_id}"
    )['libraries']
