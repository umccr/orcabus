from .base import SerializersBase
from app.models import Sample


class SampleBaseSerializer(SerializersBase):
    prefix = Sample.orcabus_id_prefix


class SampleSerializer(SampleBaseSerializer):
    class Meta:
        model = Sample
        fields = "__all__"


class SampleDetailSerializer(SampleBaseSerializer):
    from .library import LibrarySerializer

    class Meta:
        model = Sample
        fields = '__all__'

    library_set = LibrarySerializer(many=True, read_only=True)
