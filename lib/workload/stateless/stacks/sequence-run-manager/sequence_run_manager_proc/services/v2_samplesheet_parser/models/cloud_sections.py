#!/usr/bin/env python3

# Imports
from typing import Optional, Dict
from pydantic import BaseModel, RootModel
from sequence_run_manager_proc.services.v2_samplesheet_parser.models.base_model import SampleSheetSectionBaseModel

class CloudSettingsBase(BaseModel):
    cloud_workflow: str
    generated_version: Optional[str]
    
class CloudSettingsModel(RootModel):
    """
    The CloudSettings Section
    https://help.ica.illumina.com/sequencer-integration/analysis_autolaunch#secondary-analysis-settings
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure/section-requirements
    """
    root: Dict[str,str]

    def __init__(self, **kwargs):
        # Separate pipeline URNs from other settings
        analysis_urns = {
            k: v for k, v in kwargs.items() if k.lower().endswith("_pipeline") and v.lower().startswith("urn:")
        }
        base_settings = {
            k: v for k, v in kwargs.items() if not k in analysis_urns
        }
        base = CloudSettingsBase(**base_settings)
        
        #combine base settings with analysis urns
        all_settings = {
            **base.model_dump(),
            **analysis_urns
        }
        super().__init__(**all_settings)


class CloudDataModel(SampleSheetSectionBaseModel):
    """
    The CloudData Section
    https://help.ica.illumina.com/sequencer-integration/analysis_autolaunch#secondary-analysis-settings
    https://support-docs.illumina.com/SW/DRAGEN_TSO500_v2.1_ICA/Content/LP/TSO500/AutolaunchSampleSheetSettings.htm
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure/section-requirements
    """
    sample_id: Optional[str] = None
    project_name: Optional[str] = None
    library_name: Optional[str] = None
    library_prep_kit_name: Optional[str] = None
    index_adapter_kit_name: Optional[str] = None
