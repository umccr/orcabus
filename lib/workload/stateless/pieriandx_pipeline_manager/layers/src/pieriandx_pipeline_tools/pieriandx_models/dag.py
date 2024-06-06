#!/usr/bin/env python3

from typing import Dict
from pydantic import BaseModel, ConfigDict


class Dag(BaseModel):
    # Attributes
    name: str
    description: str

    # Model configuration
    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> Dict:
        return {
            "dagDescription": self.description,
            "dagName": self.name,
        }
