from pydantic import BaseModel

class SampleSheetSectionBaseModel(BaseModel):
    """
    Base model for all sample sheet section models
    """
    model_config = {
        "extra": "allow", # allow extra fields to avoid strict validation
        "validate_assignment": True, # validate assignments
        "str_strip_whitespace": True, # strip whitespace from strings
    }
    
    # custom model_dump method to remove None values when dumping to dict
    def model_dump(self, *args, **kwargs):
        exclude_none = kwargs.pop("exclude_none", True)
        if exclude_none:
            return super().model_dump(exclude_none=True, *args, **kwargs)
        return super().model_dump(*args, **kwargs)
