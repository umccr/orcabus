#!/usr/bin/env python3
from typing import Dict
from pydantic import BaseModel, ConfigDict


class Physician(BaseModel):
    # Attributes
    first_name: str
    last_name: str

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> Dict:
        return {
            "firstName": self.first_name,
            "lastName": self.last_name
        }
