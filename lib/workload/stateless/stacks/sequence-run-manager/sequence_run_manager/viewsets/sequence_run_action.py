import json
import base64
import ulid
from datetime import datetime, timezone
from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer

from sequence_run_manager.models import Sequence, Comment
from sequence_run_manager.serializers import SequenceSerializer
from sequence_run_manager.aws_event_bridge.event_srv import emit_srm_api_event

from v2_samplesheet_parser.functions.retriever import retrieve_library_from_csv_samplesheet


class SequenceRunActionViewSet(ViewSet):
    """
    ViewSet for sequence run actions
    
    add_samplesheet:
        upload sample sheet for a sequence run
    """

    @extend_schema(
        responses=OpenApiTypes.OBJECT,
        description="Creating a fake sequence run and associate a samplesheet to it by emitting an SRSSC and/or SRLLC event to EventBridge (Orcabus)"
    )
    @action(detail=True,methods=['post'],url_name='add_samplesheet',url_path='add_samplesheet')
    def add_samplesheet(self, request, *args, **kwargs):
        """
        upload sample sheet for a sequence run
        """
        # get uploaded samplesheet
        uploaded_samplesheet = request.FILES.get('file')
        if not uploaded_samplesheet:
            return Response({"detail": "No samplesheet uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        samplesheet_name = uploaded_samplesheet.name
        instrument_run_id = request.POST.get('instrument_run_id')
        if not instrument_run_id:
            return Response({"detail": "instrument_run_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        created_by = request.POST.get('created_by')
        if not created_by:
            return Response({"detail": "created_by is required"}, status=status.HTTP_400_BAD_REQUEST)
        comment = request.POST.get('comment')
        if not comment:
            return Response({"detail": "comment is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # step 1: create a fake sequence run
        sequence_run = Sequence(
            instrument_run_id=instrument_run_id,
            sequence_run_id="r."+ulid.new().str,
            sample_sheet_name=samplesheet_name,
        )
        sequence_run.save()
        
        # step 2: read the uploaded samplesheet, and encodeed with base64
        samplesheet_content = ''
        with uploaded_samplesheet.open('rb') as f:
            samplesheet_content = f.read()
        samplesheet_base64 = base64.b64encode(samplesheet_content).decode('utf-8')
        
        # step 3: construct event bridge detail
        samplesheet_change_eb_payload = construct_samplesheet_change_eb_payload(sequence_run, samplesheet_base64, comment, created_by)
        
        # step 4: emit event to event bridge
        emit_srm_api_event(samplesheet_change_eb_payload)
        
        # step 5: check if there is library linking change
        linking_libraries = retrieve_library_from_csv_samplesheet(samplesheet_content)
        if linking_libraries:
            # step 6: emit library linking change event to event bridge
            library_linking_change_eb_payload = construct_library_linking_change_eb_payload(sequence_run, linking_libraries)
            emit_srm_api_event(library_linking_change_eb_payload)

        return Response({"detail": "Samplesheet added successfully"}, status=status.HTTP_200_OK)


def construct_samplesheet_change_eb_payload(sequence_run: Sequence, samplesheet_base64: str, comment: str, created_by: str) -> dict:
    """
    Construct event bridge detail for samplesheet change based on the sequence run and samplesheet base64
    """
    return {
        "eventType": "SequenceRunSampleSheetChange",
        "instrumentRunId": sequence_run.instrument_run_id,
        "sequenceRunId": sequence_run.sequence_run_id,
        "sequenceOrcabusId": sequence_run.orcabus_id,
        "timeStamp": datetime.now(),
        "sampleSheetName": sequence_run.sample_sheet_name,
        "samplesheetbase64gz": samplesheet_base64,
        "comment":{
            "comment": comment,
            "created_by": created_by,
            "created_at": datetime.now()
        }
    }


def construct_library_linking_change_eb_payload(sequence_run: Sequence, linked_libraries: list) -> dict:
    """
    Construct event bridge detail for library linking change based on the sequence run and linked libraries
    """
    return {
        "eventType": "SequenceRunLibraryLinkingChange",
        "instrumentRunId": sequence_run.instrument_run_id,
        "sequenceRunId": sequence_run.sequence_run_id,
        "sequenceOrcabusId": sequence_run.orcabus_id,
        "timeStamp": datetime.now(),
        "linkedLibrary": linked_libraries,
    }
