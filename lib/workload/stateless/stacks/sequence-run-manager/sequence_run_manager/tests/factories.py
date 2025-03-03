from enum import Enum

import factory
from django.utils import timezone

from sequence_run_manager.models.sequence import Sequence, SequenceStatus

utc_now_ts = int(timezone.now().replace(tzinfo=timezone.utc).timestamp())


class TestConstant(Enum):
    sequence_run_id = "r.ACGTlKjDgEy099ioQOeOWg"
    instrument_run_id = "200508_A01052_0001_BH5LY7ACGT"

class SequenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sequence
    
    sequence_run_id = TestConstant.sequence_run_id.value # unique key, legacy `run_id`
    #  status is not nullable, so we need to set it to a valid value
    status = SequenceStatus.STARTED
    start_time = timezone.make_aware(timezone.now())
    end_time = None
    
    instrument_run_id = TestConstant.instrument_run_id.value
    reagent_barcode = "NV9999999-RGSBS"
    flowcell_barcode = "BARCODEEE"
    sample_sheet_name = "SampleSheet.csv"
    
    run_volume_name = "bssh.acgtacgt498038ed99fa94fe79523959"
    run_folder_path = f"/Runs/{instrument_run_id}_{sequence_run_id}"
    run_data_uri = f"gds://{run_volume_name}{run_folder_path}"
    
    api_url = f"https://api.aps2.sh.basespace.illumina.com/v2/runs/{sequence_run_id}"
    v1pre3_id = "1234567890"
    ica_project_id = "12345678-53ba-47a5-854d-e6b53101adb7"
    
    sequence_run_name = instrument_run_id
    api_url = "https://bssh.dev/api/v1/runs/r.ACGTlKjDgEy099ioQOeOWg"
    v1pre3_id = "1234567890"
    ica_project_id = "12345678-53ba-47a5-854d-e6b53101adb7"
    experiment_name = "ExperimentName"
