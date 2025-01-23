from rest_framework.serializers import ModelSerializer

from app.models import Sample
from app.serializers.utils import OrcabusIdSerializerMetaMixin


class SampleSerializer(ModelSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Sample
        fields = "__all__"


class SampleDetailSerializer(ModelSerializer):
    from .library import LibrarySerializer

    class Meta(OrcabusIdSerializerMetaMixin):
        model = Sample
        fields = '__all__'

    library_set = LibrarySerializer(many=True, read_only=True)


class SampleHistorySerializer(ModelSerializer):

    class Meta:
        model = Sample.history.model
        fields = "__all__"
