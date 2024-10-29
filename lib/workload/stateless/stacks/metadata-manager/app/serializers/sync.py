from rest_framework import serializers


class SyncGSheetSerializer(serializers.Serializer):
    year = serializers.CharField(required=True, max_length=4, min_length=4)


class SyncCustomCsvSerializer(serializers.Serializer):
    presigned_url = serializers.URLField(required=True)
