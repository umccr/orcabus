from django.db import models, connection
from django.db.models import QuerySet, Value, Max, OuterRef, Subquery
from django.db.models.aggregates import Count
from django.db.models.functions import Concat

from library_manager.models.base import OrcaBusBaseModel, OrcaBusBaseManager


class LibraryType(models.TextChoices):
    CT_DNA = "ctDNA"
    CT_TSO = "ctTSO"
    EXOME = "exome"
    OTHER = "other"
    TEN_X = "10X"
    TSO_DNA = "TSO-DNA"
    TSO_RNA = "TSO-RNA"
    WGS = "WGS"
    WTS = "WTS"


class LibraryPhenotype(models.TextChoices):
    N_CONTROL = "negative-control"
    NORMAL = "normal"
    TUMOR = "tumor"


class LibraryAssay(models.TextChoices):
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


class LibraryQuality(models.TextChoices):
    BORDERLINE = "borderline"
    GOOD = "good"
    POOR = "poor"
    VERY_POOR = "VeryPoor"


class LibrarySource(models.TextChoices):
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


class LibraryWorkflow(models.TextChoices):
    BCL = "bcl"
    CLINICAL = "clinical"
    CONTROL = "control"
    MANUAL = "manual"
    QC = "qc"
    RESEARCH = "research"


# TODO: Possibly to get sequenced library from the API and searched this libraries in this library Model
def remove_not_sequenced(qs: QuerySet) -> QuerySet:
    # # filter library to those entries that were sequenced, i.e. have a LibraryRun entry
    # inner_qs = LibraryRun.objects.values_list('library_id', flat=True)
    # qs = qs.filter(library_id__in=inner_qs)

    # 1. Fetch the sequenced libraries from the library_run API
    # 2. Filter the library which contain the sequenced libraryRun

    return qs


def filter_only_latest_library_id(qs: QuerySet) -> QuerySet:
    """
    This function will reduce the QuerySet to only show the latest library_id in record

    :param qs: Initial QuerySet
    :return: The filtered QuerySet
    """
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


class LibraryManager(OrcaBusBaseManager):
    def get_by_keyword(self, **kwargs) -> QuerySet:
        """
        Get QuerySet based on given keyword to filter the result.

        E.g. get_by_keyword(library_id="L001", library_id="L002"), this will
        filter the querySet to show matched on library_id "L001" and "L002"

        :param show_history: The option to show history on the specific library_id
        :param sequenced: The option to filter only for sequenced library
        :return qs: A filtered django QuerySet from the Library Model
        """
        qs: QuerySet = super().get_queryset()

        # If history of the db is NOT requested filter the rest
        show_history = kwargs.pop("show_history", False)
        if not show_history:
            # GroupBy "library_id" and return the latest in record
            qs = filter_only_latest_library_id(qs)

        # If only records for sequenced libs are requested, remove the ones that are not
        sequenced = kwargs.pop("sequenced", False)
        if sequenced:
            qs = remove_not_sequenced(qs)

        # Filter with any other keywords
        qs = self.get_model_fields_query(qs, **kwargs)

        return qs

    def get_single(self, **kwargs):
        """
        Typically this is the same as the default Django `.get` function,
        but it will do a distinct filter to pick the latest library_id in record
        """
        qs: QuerySet = super().get_queryset()
        qs = filter_only_latest_library_id(qs)

        return qs.get(**kwargs)

    def get_by_aggregate_count(self, field):
        return self.values(field).annotate(count=Count(field)).order_by(field)

    def get_by_cube(self, field_left, field_right, field_sort):
        return (
            self.values(field_left, field_right)
            .annotate(count=Count(1))
            .order_by(field_sort)
        )


class Library(OrcaBusBaseModel):
    """
    Models a row in the lab tracking sheet data. Fields are the columns.

    This will store all records (including changes at given timestamp) in the database.
    """

    # Portal internal auto incremental PK ID. Scheme may change as need be and may rebuild thereof.
    # External system or business logic should not rely upon this ID field.
    # Use any of unique fields or <>_id fields below.
    id = models.BigAutoField(primary_key=True)

    # TODO: as far as Clarity is concerned, "external" lib id = tracking sheet.
    #  do we want to store clarity-generated lib id, and what do we want to call it?
    # external_library_id = models.CharField(max_length=255)

    timestamp = models.DateTimeField(editable=False)

    library_id = models.CharField(max_length=255)
    sample_name = models.CharField(max_length=255, null=True, blank=True)
    sample_id = models.CharField(max_length=255)
    external_sample_id = models.CharField(max_length=255, null=True, blank=True)
    subject_id = models.CharField(max_length=255, null=True, blank=True)
    external_subject_id = models.CharField(max_length=255, null=True, blank=True)

    phenotype = models.CharField(choices=LibraryPhenotype.choices, max_length=255)
    quality = models.CharField(choices=LibrarySource.choices, max_length=255)
    source = models.CharField(choices=LibrarySource.choices, max_length=255)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    project_owner = models.CharField(max_length=255, null=True, blank=True)
    experiment_id = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(choices=LibraryType.choices, max_length=255)
    assay = models.CharField(choices=LibraryAssay.choices, max_length=255)
    override_cycles = models.CharField(max_length=255, null=True, blank=True)
    workflow = models.CharField(choices=LibraryWorkflow.choices, max_length=255)
    coverage = models.CharField(max_length=255, null=True, blank=True)
    truseqindex = models.CharField(max_length=255, null=True, blank=True)

    objects = LibraryManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "timestamp",
                    "library_id",
                    "sample_id",
                ],
                name="library_id and sample_id must be unique at a given timestamp",
            )
        ]

    def __str__(self):
        return f"""id={self.id}, library_id={self.library_id}, sample_id={self.sample_id}, subject_id={self.subject_id},  timestamp={self.timestamp}"""

    @classmethod
    def get_table_name(cls):
        return cls._meta.db_table

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {cls.get_table_name()};")
