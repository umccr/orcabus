from datetime import datetime, timezone
from enum import Enum

import factory

from library_manager.models.library import Library, LibraryType, LibraryPhenotype


utc_now_ts = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())


class TestConstant(Enum):
    wfr_id = f"wfr.j317paO8zB6yG25Zm6PsgSivJEoq4Ums"
    wfr_id2 = f"wfr.Q5555aO8zB6yG25Zm6PsgSivGwDx_Uaa"
    wfv_id = f"wfv.TKWp7hsFnVTCE8KhfXEurUfTCqSa6zVx"
    wfl_id = f"wfl.Dc4GzACbjhzOf3NbqAYjSmzkE1oWKI9H"
    umccrise_wfr_id = f"wfr.umccrisezB6yG25Zm6PsgSivJEoq4Ums"
    umccrise_wfv_id = f"wfv.umccrisenVTCE8KhfXEurUfTCqSa6zVx"
    umccrise_wfl_id = f"wfl.umccrisejhzOf3NbqAYjSmzkE1oWKI9H"
    rnasum_wfr_id = f"wfr.rnasumzB6yG25Zm6PsgSivJEoq4Ums"
    rnasum_wfv_id = f"wfv.rnasumnVTCE8KhfXEurUfTCqSa6zVx"
    rnasum_wfl_id = f"wfl.rnasumjhzOf3NbqAYjSmzkE1oWKI9H"
    version = "v1"
    instrument_run_id = "200508_A01052_0001_BH5LY7ACGT"
    instrument_run_id2 = "220101_A01052_0002_XR5LY7TGCA"
    sqr_name = instrument_run_id
    run_id = "r.ACGTlKjDgEy099ioQOeOWg"
    run_id2 = "r.GACTlKjDgEy099io_0000"
    override_cycles = "Y151;I8;I8;Y151"
    subject_id = "SBJ00001"
    library_id_normal = "L2100001"
    lane_normal_library = 1
    library_id_tumor = "L2100002"
    lane_tumor_library = 3
    sample_id = "PRJ210001"
    sample_name_normal = f"{sample_id}_{library_id_normal}"
    sample_name_tumor = f"{sample_id}_{library_id_tumor}"
    wts_library_id_tumor = "L2100003"
    wts_library_id_tumor2 = "L2200001"
    wts_lane_tumor_library = 4
    wts_sample_id = "MDX210002"


class LibraryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Library

    library_id = TestConstant.library_id_normal.value
    sample_name = "Ambiguous Sample"
    sample_id = TestConstant.sample_id.value
    external_sample_id = "DNA123456"
    subject_id = TestConstant.subject_id.value
    external_subject_id = "PM1234567"
    phenotype = LibraryPhenotype.NORMAL.value
    quality = "good"
    source = "blood"
    project_name = "CUP"
    project_owner = "UMCCR"
    experiment_id = "TSqN123456LL"
    type = "WGS"
    assay = "TsqNano"
    override_cycles = TestConstant.override_cycles.value
    workflow = "clinical"
    coverage = "40.0"
    truseqindex = "A09"
    timestamp = datetime.now(tz=timezone.utc)


class TumorLibraryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Library

    library_id = TestConstant.library_id_tumor.value
    sample_name = "Ambiguous Sample"
    sample_id = TestConstant.sample_id.value
    external_sample_id = "DNA123456"
    subject_id = TestConstant.subject_id.value
    external_subject_id = "PM1234567"
    phenotype = LibraryPhenotype.TUMOR.value
    quality = "good"
    source = "blood"
    project_name = "CUP"
    project_owner = "UMCCR"
    experiment_id = "TSqN123456LL"
    type = "WGS"
    assay = "TsqNano"
    override_cycles = TestConstant.override_cycles.value
    workflow = "clinical"
    coverage = "40.0"
    truseqindex = "A09"


class WtsTumorLibraryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Library

    library_id = TestConstant.wts_library_id_tumor.value
    sample_name = "Ambiguous WTS Sample"
    sample_id = TestConstant.wts_sample_id.value
    external_sample_id = "RNA123456"
    subject_id = TestConstant.subject_id.value
    external_subject_id = "PM1234567"
    phenotype = LibraryPhenotype.TUMOR.value
    quality = "good"
    source = "blood"
    project_name = "CUP"
    project_owner = "UMCCR"
    experiment_id = "TSqN123456LL"
    type = LibraryType.WTS.value
    assay = "NebRNA"
    override_cycles = TestConstant.override_cycles.value
    workflow = "clinical"
    coverage = "40.0"
    truseqindex = "A09"


class WtsTumorLibraryFactory2(factory.django.DjangoModelFactory):
    class Meta:
        model = Library

    library_id = TestConstant.wts_library_id_tumor2.value
    sample_name = "Ambiguous WTS Sample 2"
    sample_id = TestConstant.wts_sample_id.value
    external_sample_id = "RNA123456"
    subject_id = TestConstant.subject_id.value
    external_subject_id = "PM1234567"
    phenotype = LibraryPhenotype.TUMOR.value
    quality = "good"
    source = "blood"
    project_name = "CUP"
    project_owner = "UMCCR"
    experiment_id = "TSqN123456LL"
    type = LibraryType.WTS.value
    assay = "NebRNA"
    override_cycles = TestConstant.override_cycles.value
    workflow = "clinical"
    coverage = "40.0"
    truseqindex = "A09"
