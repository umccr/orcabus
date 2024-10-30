import os
import json
from libumccr.aws import lambda_client
from drf_spectacular.types import OpenApiTypes

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from app.serializers.sync import SyncGSheetSerializer, SyncCustomCsvSerializer


class SyncViewSet(ViewSet):

    @extend_schema(
        request=SyncGSheetSerializer,
        responses=OpenApiTypes.STR,
        description="Sync metadata with the Google tracking sheet"
    )
    @action(
        detail=False,
        methods=['post'],
        url_name='gsheet',
        url_path='gsheet'
    )
    def sync_gsheet(self, request):
        lambda_function_name = os.environ.get('SYNC_GSHEET_LAMBDA_NAME', None)
        serializer = SyncGSheetSerializer(data=request.data)

        if lambda_function_name is None:
            raise Exception("Lambda name is not set in the environment variable")

        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        lambda_client().invoke(
            FunctionName=lambda_function_name,
            InvocationType='Event',
            Payload=json.dumps({
                "year": serializer.data['year']
            })
        )

        return Response("Syncing the tracking sheet with the Google Sheet has been initiated.")

    @extend_schema(
        request=SyncCustomCsvSerializer,
        responses=OpenApiTypes.STR,
        description="Sync metadata from the provided csv presigned url."
    )
    @action(
        detail=False,
        methods=['post'],
        url_name='presigned-csv',
        url_path='presigned-csv'
    )
    def sync_custom_csv(self, request):
        lambda_function_name = os.environ.get('SYNC_CSV_PRESIGNED_URL_LAMBDA_NAME', None)
        serializer = SyncCustomCsvSerializer(data=request.data)

        if lambda_function_name is None:
            raise Exception("Lambda name is not set in the environment variable")

        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        lambda_client().invoke(
            FunctionName=lambda_function_name,
            InvocationType='Event',
            Payload=json.dumps({
                "url": serializer.data['presigned_url']
            })
        )

        return Response("Start syncing metadata with the provided csv presigned url.")
