from workflow_manager.serializers.base import SerializersBase
from workflow_manager.models import Library


class LibraryBaseSerializer(SerializersBase):
    prefix = Library.orcabus_id_prefix


class LibrarySerializer(LibraryBaseSerializer):
    class Meta:
        model = Library
        fields = "__all__"
