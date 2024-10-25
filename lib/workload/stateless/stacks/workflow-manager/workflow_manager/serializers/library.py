from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin
from workflow_manager.models import Library


class LibraryBaseSerializer(SerializersBase):
    prefix = Library.orcabus_id_prefix

class LibraryListParamSerializer(OptionalFieldsMixin, LibraryBaseSerializer):
    class Meta:
        model = Library
        fields = "__all__"

class LibrarySerializer(LibraryBaseSerializer):
    class Meta:
        model = Library
        fields = "__all__"
