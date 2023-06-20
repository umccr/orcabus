from typing import Dict, List

from rest_framework import serializers
from rest_framework.fields import empty

from metadata_manager.models.metadata import Metadata

READ_ONLY_SERIALIZER = "READ ONLY SERIALIZER"


class MetadataSyncSerializer(serializers.Serializer):
    sheets = serializers.ListField(
        default=["2019", "2020", "2021", "2022", "2023"]
    )  # OpenAPI swagger doc hint only
    truncate = serializers.BooleanField(default=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubjectIdSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return instance.subject_id

    def to_internal_value(self, data):
        raise NotImplementedError(READ_ONLY_SERIALIZER)

    def update(self, instance, validated_data):
        raise NotImplementedError(READ_ONLY_SERIALIZER)

    def create(self, validated_data):
        raise NotImplementedError(READ_ONLY_SERIALIZER)


class MetadataModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metadata
        fields = "__all__"
