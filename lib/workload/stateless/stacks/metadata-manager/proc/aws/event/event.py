import os
import json
from typing import Literal

from app.serializers.utils import to_camel_case_key_dict
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
        # Below must be in camelCase as what we agreed (and written in docs) in API level
        self.detail = json.dumps({
            "action": action,
            "model": model,
            "refId": ref_id,
            "data": Marshaller.marshall(to_camel_case_key_dict(data))
        })

    def __str__(self):
        return self.__dict__

    def get_put_event_entry(self):
        return {
            "Source": self.namespace,
            "DetailType": self.detail_type,
            "Detail": self.detail,
            "EventBusName": self.event_bus_name
        }
