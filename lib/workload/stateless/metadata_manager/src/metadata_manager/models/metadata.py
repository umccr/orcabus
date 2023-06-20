from django.db import models, connection
from django.db.models import QuerySet, Value, Max, OuterRef, Subquery
from django.db.models.aggregates import Count
from django.db.models.functions import Concat

from metadata_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class MetadataType(models.TextChoices):
    CT_DNA = "ctDNA"
    CT_TSO = "ctTSO"
    EXOME = "exome"
    OTHER = "other"
    TEN_X = "10X"
    TSO_DNA = "TSO-DNA"
    TSO_RNA = "TSO-RNA"
    WGS = "WGS"
    WTS = "WTS"


class MetadataPhenotype(models.TextChoices):
    N_CONTROL = "negative-control"
    NORMAL = "normal"
    TUMOR = "tumor"


class MetadataAssay(models.TextChoices):
    AG_SS_CRE = "AgSsCRE"
    CT_TSO = "ctTSO"
    NEB_DNA = "NebDNA"
    NEB_DNA_U = "NebDNAu"
    NEB_RNA = "NebRNA"
    PCR_FREE = "PCR-Free-Tagmentation"
    TEN_X_3PRIME = "10X-3prime-expression"
    TEN_X_5PRIME = "10X-5prime-expression"
    TEN_X_ATAC = "10X-ATAC"
    TEN_X_CITE_FEAT = "10X-CITE-feature"
    TEN_X_CITE_HASH = "10X-CITE-hashing"
    TEN_X_CNV = "10X-CNV"
    TEN_X_VDJ = "10X-VDJ"
    TEN_X_VDJ_TCR = "10X-VDJ-TCR"
    TSO_DNA = "TSODNA"
    TSO_RNA = "TSORNA"
    TSQ_NANO = "TsqNano"
    TSQ_STR = "TsqSTR"


class MetadataQuality(models.TextChoices):
    BORDERLINE = "borderline"
    GOOD = "good"
    POOR = "poor"
    VERY_POOR = "VeryPoor"


class MetadataSource(models.TextChoices):
    ACITES = "ascites"
    BLOOD = "blood"
    BONE = "bone-marrow"
    BUCCAL = "buccal"
    CELL_LINE = "cell-line"
    CF_DNA = "cfDNA"
    CYST = "cyst-fluid"
    DNA = "DNA"
    EYEBROW = "eyebrow-hair"
    FFPE = "FFPE"
    FNA = "FNA"
    OCT = "OCT"
    ORGANOID = "organoid"
    PDX = "PDX-tissue"
    PLASMA = "plasma-serum"
    RNA = "RNA"
    TISSUE = "tissue"
    WATER = "water"


class MetadataWorkflow(models.TextChoices):
    BCL = "bcl"
    CLINICAL = "clinical"
    CONTROL = "control"
    MANUAL = "manual"
    QC = "qc"
    RESEARCH = "research"


# TODO: Possibly to get sequenced library from the API and searched this libraries in this metadata Model
def remove_not_sequenced(qs: QuerySet) -> QuerySet:
    # # filter metadata to those entries that were sequenced, i.e. have a LibraryRun entry
    # inner_qs = LibraryRun.objects.values_list('library_id', flat=True)
    # qs = qs.filter(library_id__in=inner_qs)

    # 1. Fetch the sequenced libraries from the library_run API
    # 2. Filter the metadata which contain the sequenced libraryRun

    return qs


def filter_only_latest_library_id(qs: QuerySet) -> QuerySet:
    qs = qs.filter(
        id__in=qs.values("library_id")
        .annotate(
            latest_id=Subquery(
                qs.filter(library_id=OuterRef("library_id"))
                .order_by("-timestamp")
                .values("id")[:1]
            )
        )
        .values("latest_id")
    )

    return qs


class MetadataManager(OrcaBusBaseManager):
    def get_by_keyword(self, **kwargs) -> QuerySet:
        qs: QuerySet = super().get_queryset()

        qs = self.get_model_fields_query(qs, **kwargs)

        # GroupBy "library_id" and return the latest in record
        qs = filter_only_latest_library_id(qs)

        # if only records for sequenced libs are requested, remove the ones that are not
        sequenced = kwargs.pop("sequenced", False)
        if sequenced:
            qs = remove_not_sequenced(qs)

        return qs

    # TODO: Will enforce to use 'get_by_keyword' function instead
    # def get_by_keyword_in(self, **kwargs) -> QuerySet:
    #     qs: QuerySet = self.all()
    #
    #     subjects = kwargs.get('subjects', None)
    #     if subjects:
    #         qs = qs.filter(subject_id__in=subjects)
    #
    #     samples = kwargs.get('samples', None)
    #     if samples:
    #         qs = qs.filter(sample_id__in=samples)
    #
    #     libraries = kwargs.get('libraries', None)
    #     if libraries:
    #         qs = qs.filter(library_id__in=libraries)
    #
    #     phenotypes = kwargs.get('phenotypes', None)
    #     if phenotypes:
    #         qs = qs.filter(phenotype__in=phenotypes)
    #
    #     types = kwargs.get('types', None)
    #     if types:
    #         qs = qs.filter(type__in=types)
    #
    #     workflows = kwargs.get('workflows', None)
    #     if workflows:
    #         qs = qs.filter(workflow__in=workflows)
    #
    #     project_names = kwargs.get('project_names', None)
    #     if project_names:
    #         qs = qs.filter(project_name__in=project_names)
    #
    #     project_owners = kwargs.get('project_owners', None)
    #     if project_owners:
    #         qs = qs.filter(project_owner__in=project_owners)
    #
    #     # sequenced = kwargs.get('sequenced', False)
    #     # if sequenced:
    #     #     qs = remove_not_sequenced(qs)
    #
    #     return qs

    # TODO: Consider to deprecate this
    # def get_by_sample_library_name(self, sample_library_name, sequenced: bool = False) -> QuerySet:
    #     """
    #     Here we project (or annotate) virtual attribute called "sample_library_name" which is using database built-in
    #     concat function of two existing columns sample_id and library_id.
    #
    #     :param sample_library_name:
    #     :param sequenced: Boolean to indicate whether to only return metadata for sequenced libraries
    #     :return: QuerySet
    #     """
    #     qs: QuerySet = self.annotate(sample_library_name=Concat('sample_id', Value('_'), 'library_id'))
    #     qs = qs.filter(sample_library_name__iexact=sample_library_name)
    #
    #     # if sequenced:
    #     #     qs = remove_not_sequenced(qs)
    #
    #     return qs

    def get_by_aggregate_count(self, field):
        return self.values(field).annotate(count=Count(field)).order_by(field)

    def get_by_cube(self, field_left, field_right, field_sort):
        return (
            self.values(field_left, field_right)
            .annotate(count=Count(1))
            .order_by(field_sort)
        )


class Metadata(OrcaBusBaseModel):
    """
    Models a row in the lab tracking sheet data. Fields are the columns.
    """

    # Portal internal auto incremental PK ID. Scheme may change as need be and may rebuild thereof.
    # External system or business logic should not rely upon this ID field.
    # Use any of unique fields or <>_id fields below.
    id = models.BigAutoField(primary_key=True)

    # TODO: as far as Clarity is concerned, "external" lib id = tracking sheet.
    #  do we want to store clarity-generated lib id, and what do we want to call it?
    # external_library_id = models.CharField(max_length=255)

    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    library_id = models.CharField(max_length=255)
    sample_name = models.CharField(max_length=255, null=True, blank=True)
    sample_id = models.CharField(max_length=255)
    external_sample_id = models.CharField(max_length=255, null=True, blank=True)
    subject_id = models.CharField(max_length=255, null=True, blank=True)
    external_subject_id = models.CharField(max_length=255, null=True, blank=True)

    phenotype = models.CharField(choices=MetadataPhenotype.choices, max_length=255)
    quality = models.CharField(choices=MetadataSource.choices, max_length=255)
    source = models.CharField(choices=MetadataSource.choices, max_length=255)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    project_owner = models.CharField(max_length=255, null=True, blank=True)
    experiment_id = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(choices=MetadataType.choices, max_length=255)
    assay = models.CharField(choices=MetadataAssay.choices, max_length=255)
    override_cycles = models.CharField(max_length=255, null=True, blank=True)
    workflow = models.CharField(choices=MetadataWorkflow.choices, max_length=255)
    coverage = models.CharField(max_length=255, null=True, blank=True)
    truseqindex = models.CharField(max_length=255, null=True, blank=True)

    objects = MetadataManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "timestamp",
                    "library_id",
                    "sample_id",
                ],
                name="library_id and sample_id be unique at a given timestamp",
            )
        ]

    def __str__(self):
        return f"""id={self.id}, library_id={self.library_id}, sample_id={self.sample_id}, subject_id={self.subject_id},  created={self.timestamp}"""

    @classmethod
    def get_table_name(cls):
        return cls._meta.db_table

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {cls.get_table_name()};")
