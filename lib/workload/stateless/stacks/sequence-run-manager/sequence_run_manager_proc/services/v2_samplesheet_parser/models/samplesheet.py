from pydantic import BaseModel  
from typing import Optional, List

from .run_info_sections import HeaderModel, ReadsModel, SequencingModel
from .bcl_convert_sections import BCLConvertSettingsModel, BCLConvertDataModel
from .cloud_sections import CloudSettingsModel, CloudDataModel
from .tso500l_sections import TSO500LSettingsModel, TSO500LDataModel
from .tso500s_sections import TSO500SSettingsModel, TSO500SDataModel

class SampleSheetModel(BaseModel):
    """
    The SampleSheet Model
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure
    """
    # Run Info Sections
    header: HeaderModel
    reads: ReadsModel
    sequencing: Optional[SequencingModel] = None

    # BCLConvert Sections
    bclconvert_settings: Optional[BCLConvertSettingsModel] = None
    bclconvert_data: Optional[List[BCLConvertDataModel]] = None

    # Cloud Sections
    cloud_settings: Optional[CloudSettingsModel] = None
    cloud_data: Optional[List[CloudDataModel]] = None

    # TSO500L Sections
    tso500l_settings: Optional[TSO500LSettingsModel] = None
    tso500l_data: Optional[List[TSO500LDataModel]] = None
    cloud_tso500l_settings: Optional[TSO500LSettingsModel] = None
    cloud_tso500l_data: Optional[List[TSO500LDataModel]] = None

    # TSO500S Sections
    tso500s_settings: Optional[TSO500SSettingsModel] = None
    tso500s_data: Optional[List[TSO500SDataModel]] = None
    cloud_tso500s_settings: Optional[TSO500SSettingsModel] = None
    cloud_tso500s_data: Optional[List[TSO500SDataModel]] = None
    
    # custom model_dump method to remove None values when dumping to dict
    def model_dump(self, *args, **kwargs):
        exclude_none = kwargs.pop("exclude_none", True)
        if exclude_none:
            return super().model_dump(exclude_none=True, *args, **kwargs)
        return super().model_dump(*args, **kwargs)

