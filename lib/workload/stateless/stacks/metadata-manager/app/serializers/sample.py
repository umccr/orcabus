from rest_framework import serializers

from app.models import Sample


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"
