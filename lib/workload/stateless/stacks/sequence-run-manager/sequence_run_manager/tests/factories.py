from datetime import datetime, timezone
from enum import Enum

import factory
from django.utils.timezone import make_aware

from sequence_run_manager.models.sequence import Sequence, SequenceStatus

utc_now_ts = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())


class TestConstant(Enum):
    instrument_run_id = "200508_A01052_0001_BH5LY7ACGT"


class SequenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sequence

    instrument_run_id = TestConstant.instrument_run_id.value
    run_volume_name = "bssh.acgtacgt498038ed99fa94fe79523959"
    run_folder_path = f"/Runs/{instrument_run_id}_r.ACGTlKjDgEy099ioQOeOWg"
    run_data_uri = f"gds://{run_volume_name}{run_folder_path}"
    status = SequenceStatus.STARTED
    start_time = make_aware(datetime.utcnow())
    end_time = None

    reagent_barcode = "NV9999999-RGSBS"
    flowcell_barcode = "BARCODEEE"
    sample_sheet_name = "SampleSheet.csv"
    sequence_run_id = "r.ACGTlKjDgEy099ioQOeOWg"
    sequence_run_name = instrument_run_id
    api_url = "https://bssh.dev/api/v1/runs/r.ACGTlKjDgEy099ioQOeOWg"
    v1pre3_id = "1234567890"
    ica_project_id = "12345678-53ba-47a5-854d-e6b53101adb7"
    experiment_name = "ExperimentName"
