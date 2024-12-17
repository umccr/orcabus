from rest_framework.serializers import ModelSerializer

from app.models import Sample


class SampleSerializer(ModelSerializer):
    class Meta:
        model = Sample
        fields = "__all__"


class SampleDetailSerializer(ModelSerializer):
    from .library import LibrarySerializer

    class Meta:
        model = Sample
        fields = '__all__'

    library_set = LibrarySerializer(many=True, read_only=True)


class SampleHistorySerializer(ModelSerializer):

    class Meta:
        model = Sample.history.model
        fields = "__all__"
