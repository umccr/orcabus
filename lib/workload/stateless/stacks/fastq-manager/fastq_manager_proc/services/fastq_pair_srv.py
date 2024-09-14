from django.db import transaction

from fastq_manager.models.fastq_pair import FastqPair
from fastq_manager.tests.factories import FastqPairFactory


@transaction.atomic
def persist_fastq_pair():
    FastqPairFactory()


@transaction.atomic
def get_fastq_pair_from_db():
    return FastqPair.objects.first()
