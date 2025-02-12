from enum import StrEnum
from typing import Type

from rest_framework import serializers


class AllowedRerunWorkflow(StrEnum):
    RNASUM = "rnasum"


class AllowedRerunWorkflowSerializer(serializers.Serializer):
    is_valid = serializers.BooleanField()
    allowed_dataset_choice = serializers.ListField(child=serializers.CharField())
    valid_workflows = serializers.ListField(child=serializers.CharField())


class BaseRerunInputSerializer(serializers.Serializer):
    # Reruns with the same input (duplicate reruns) should not be allowed unless this flag is set to True
    allow_duplication = serializers.BooleanField(default=False, required=False,
                                                 help_text='Allow rerun with the same previous input (duplicate rerun)')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RnasumRerunInputSerializer(BaseRerunInputSerializer):
    """
    For 'rnasum' workflow rerun only allow dataset to be overridden.
    """

    # https://github.com/umccr/RNAsum/blob/master/TCGA_projects_summary.md
    allowed_dataset_choice = [
        # PRIMARY_DATASETS_OPTION
        "BRCA", "THCA", "HNSC", "LGG", "KIRC", "LUSC", "LUAD", "PRAD", "STAD", "LIHC", "COAD", "KIRP",
        "BLCA", "OV", "SARC", "PCPG", "CESC", "UCEC", "PAAD", "TGCT", "LAML", "ESCA", "GBM", "THYM",
        "SKCM", "READ", "UVM", "ACC", "MESO", "KICH", "UCS", "DLBC", "CHOL",
        # EXTENDED_DATASETS_OPTION
        "LUAD-LCNEC", "BLCA-NET",
        "PAAD-IPMN", "PAAD-NET", "PAAD-ACC",
        # PAN_CANCER_DATASETS_OPTION
        "PANCAN"
    ]

    dataset = serializers.ChoiceField(choices=allowed_dataset_choice, required=True)


RERUN_INPUT_SERIALIZERS: dict[AllowedRerunWorkflow, Type[BaseRerunInputSerializer]] = {
    AllowedRerunWorkflow.RNASUM: RnasumRerunInputSerializer,
}
