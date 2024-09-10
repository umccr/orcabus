from typing import Dict, List

from rest_framework import serializers
from rest_framework.fields import empty

from fastq_manager.models.fastq_pair import FastqPair

READ_ONLY_SERIALIZER = "READ ONLY SERIALIZER"


class FastqPairModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = FastqPair
        fields = '__all__'
