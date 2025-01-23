from workflow_manager.serializers.base import SerializersBase, OptionalFieldsMixin, OrcabusIdSerializerMetaMixin
from workflow_manager.models import Library


class LibraryBaseSerializer(SerializersBase):
    pass


class LibraryListParamSerializer(OptionalFieldsMixin, LibraryBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Library
        fields = "__all__"


class LibrarySerializer(LibraryBaseSerializer):
    class Meta(OrcabusIdSerializerMetaMixin):
        model = Library
        fields = "__all__"
