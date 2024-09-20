from .base import SerializersBase
from app.models import Sample


class SampleSerializer(SerializersBase):
    prefix = Sample.orcabus_id_prefix

    class Meta:
        model = Sample
        fields = "__all__"
