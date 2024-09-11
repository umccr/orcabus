import os
import json
from typing import Literal
from .schema.orcabus_metadatamanager.labmetadatastatechange import Marshaller

EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME")


class LabMetadataStateChangeEvent:
    namespace = "orcabus.metadatamanager"
    detail_type = "LabMetadataStateChange"
    event_bus_name = EVENT_BUS_NAME

    def __init__(self,
                 action: Literal['CREATE', 'UPDATE', 'DELETE'],
                 model: Literal['LIBRARY', 'SPECIMEN', 'SUBJECT'],
                 data: dict) -> None:
        self.detail = {
            "action": action,
            "model": model,
            "data": json.dumps(Marshaller.marshall(data))
        }

    def __str__(self):
        return self.__dict__

    def get_put_event_entry(self):
        return {
            "Source": self.namespace,
            "DetailType": self.detail_type,
            "Detail": json.dumps(self.detail),
            "EventBusName": self.event_bus_name
        }
