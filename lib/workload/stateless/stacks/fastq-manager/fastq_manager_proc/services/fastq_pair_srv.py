from django.db import transaction

from fastq_manager.models.fastq_pair import FastqPair


@transaction.atomic
def persist_hello_srv():
    fastq_pair = FastqPair(
        rgid="foo-unique-id-12345",
        rgsm="specimen.id.12345",
        rglb="library.id.12345",
        read_1_id="file.12345",
        read_2_id="file.12346",
        coverage="80X",
        quality="OK",
        is_archived=False,
        is_compressed=False
    )
    fastq_pair.save()


@transaction.atomic
def get_fastq_pair_from_db():
    return FastqPair.objects.first()
