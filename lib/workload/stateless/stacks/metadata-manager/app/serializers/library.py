from app.models import Library
from .base import SerializersBase
from .project import ProjectSerializer
from .sample import SampleSerializer
from .subject import SubjectSerializer


class LibrarySerializer(SerializersBase):
    prefix = Library.orcabus_id_prefix

    project_set = ProjectSerializer(many=True, read_only=True)

    sample = SampleSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Library
        fields = "__all__"
