from app.models import Library, Sample, Subject
from .base import SerializersBase


class LibraryBaseSerializer(SerializersBase):
    prefix = Library.orcabus_id_prefix


class LibrarySerializer(LibraryBaseSerializer):
    class Meta:
        model = Library
        exclude = ["project_set"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['sample'] = Sample.orcabus_id_prefix + representation['sample']
        representation['subject'] = Subject.orcabus_id_prefix + representation['subject']
        return representation


class LibraryDetailSerializer(LibraryBaseSerializer):
    from .sample import SampleSerializer
    from .project import ProjectSerializer
    from .subject import SubjectSerializer

    project_set = ProjectSerializer(many=True, read_only=True)

    sample = SampleSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Library
        fields = "__all__"
