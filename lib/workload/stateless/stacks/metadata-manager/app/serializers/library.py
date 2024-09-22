from app.models import Library
from .base import SerializersBase
from .project import ProjectSerializer
from .sample import SampleSerializer
from .subject import SubjectSerializer


class LibraryBaseSerializer(SerializersBase):
    prefix = Library.orcabus_id_prefix


class LibrarySerializer(LibraryBaseSerializer):
    class Meta:
        model = Library
        exclude = ["project_set"]


class LibraryDetailSerializer(LibraryBaseSerializer):
    project_set = ProjectSerializer(many=True, read_only=True)

    sample = SampleSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Library
        fields = "__all__"
