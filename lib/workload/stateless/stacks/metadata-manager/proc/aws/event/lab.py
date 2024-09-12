import os
import json
from typing import Literal
from .schema.orcabus_metadatamanager.metadatastatechange import Marshaller


class MetadataStateChangeEvent:
    namespace = "orcabus.metadatamanager"
    detail_type = "MetadataStateChange"

    def __init__(self,
                 action: Literal['CREATE', 'UPDATE', 'DELETE'],
                 model: Literal['LIBRARY', 'SPECIMEN', 'SUBJECT'],
                 ref_id: str,
                 data: dict) -> None:
        self.event_bus_name = os.getenv('EVENT_BUS_NAME', '')
        self.detail = {
            "action": action,
            "model": model,
            "ref_id": ref_id,
            "data": Marshaller.marshall(data)
        }

    def __str__(self):
        return self.__dict__

    def get_put_event_entry(self):
        return {
            "Source": self.namespace,
            "DetailType": self.detail_type,
            "Detail": self.detail,
            "EventBusName": self.event_bus_name
        }
