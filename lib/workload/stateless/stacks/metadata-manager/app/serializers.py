from rest_framework import serializers

from app.models import Subject, Specimen, Library


class LibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = "__all__"


class SpecimenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specimen
        fields = "__all__"


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class SubjectFullSerializer(serializers.ModelSerializer):
    """
    This is a full Subject serializer which include all the children's (specimen and library) related models
    """

    class SpecimenLibrarySerializer(serializers.ModelSerializer):
        """
        This is a full Specimen serializer which include the library model
        """
        library_set = LibrarySerializer(many=True)

        class Meta:
            model = Specimen
            fields = "__all__"

    specimen_set = SpecimenLibrarySerializer(many=True)

    class Meta:
        model = Subject
        fields = "__all__"


class LibraryFullSerializer(serializers.ModelSerializer):
    """
    This is a full Library serializer which include the specimen and subject models
    """

    class SpecimenSubjectSerializer(serializers.ModelSerializer):
        """
        This is a full Specimen serializer which include the subject model
        """
        subject = SubjectSerializer()

        class Meta:
            model = Specimen
            fields = "__all__"

    specimen = SpecimenSubjectSerializer(many=False)

    class Meta:
        model = Library
        fields = "__all__"
