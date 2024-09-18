import factory

from fastq_manager.models.fastq_pair import FastqPair


class FastqPairFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FastqPair

    rgid = "foo-unique-id-12345"
    rgsm = "specimen.id.12345"
    rglb = "library.id.12345"
    read_1_id = "file.12345"
    read_2_id = "file.12346"
    coverage = "80X"
    quality = "OK"
    is_archived = False
    is_compressed = False


