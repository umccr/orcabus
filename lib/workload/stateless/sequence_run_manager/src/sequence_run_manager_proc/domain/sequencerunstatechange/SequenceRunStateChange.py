# coding: utf-8
import pprint
import re  # noqa: F401

import six


class SequenceRunStateChange(object):
    _types = {
        "id": "int",
        "instrument_run_id": "str",
        "run_volume_name": "str",
        "run_folder_path": "str",
        "run_data_uri": "str",
        "status": "str",
        "start_time": "datetime",
        "end_time": "datetime",
        "reagent_barcode": "str",
        "flowcell_barcode": "str",
        "sample_sheet_name": "str",
        "sequence_run_id": "str",
        "sequence_run_name": "str",
    }

    _attribute_map = {
        "id": "id",
        "instrument_run_id": "instrument_run_id",
        "run_volume_name": "run_volume_name",
        "run_folder_path": "run_folder_path",
        "run_data_uri": "run_data_uri",
        "status": "status",
        "start_time": "start_time",
        "end_time": "end_time",
        "reagent_barcode": "reagent_barcode",
        "flowcell_barcode": "flowcell_barcode",
        "sample_sheet_name": "sample_sheet_name",
        "sequence_run_id": "sequence_run_id",
        "sequence_run_name": "sequence_run_name",
    }

    def __init__(
        self,
        id=None,
        instrument_run_id=None,
        run_volume_name=None,
        run_folder_path=None,
        run_data_uri=None,
        status=None,
        start_time=None,
        end_time=None,
        reagent_barcode=None,
        flowcell_barcode=None,
        sample_sheet_name=None,
        sequence_run_id=None,
        sequence_run_name=None,
    ):  # noqa: E501
        self._id = None
        self._instrument_run_id = None
        self._run_volume_name = None
        self._run_folder_path = None
        self._run_data_uri = None
        self._status = None
        self._start_time = None
        self._end_time = None
        self._reagent_barcode = None
        self._flowcell_barcode = None
        self._sample_sheet_name = None
        self._sequence_run_id = None
        self._sequence_run_name = None
        self.discriminator = None
        self.id = id
        self.instrument_run_id = instrument_run_id
        self.run_volume_name = run_volume_name
        self.run_folder_path = run_folder_path
        self.run_data_uri = run_data_uri
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.reagent_barcode = reagent_barcode
        self.flowcell_barcode = flowcell_barcode
        self.sample_sheet_name = sample_sheet_name
        self.sequence_run_id = sequence_run_id
        self.sequence_run_name = sequence_run_name

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    @property
    def instrument_run_id(self):
        return self._instrument_run_id

    @instrument_run_id.setter
    def instrument_run_id(self, instrument_run_id):
        self._instrument_run_id = instrument_run_id

    @property
    def run_volume_name(self):
        return self._run_volume_name

    @run_volume_name.setter
    def run_volume_name(self, run_volume_name):
        self._run_volume_name = run_volume_name

    @property
    def run_folder_path(self):
        return self._run_folder_path

    @run_folder_path.setter
    def run_folder_path(self, run_folder_path):
        self._run_folder_path = run_folder_path

    @property
    def run_data_uri(self):
        return self._run_data_uri

    @run_data_uri.setter
    def run_data_uri(self, run_data_uri):
        self._run_data_uri = run_data_uri

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, start_time):
        self._start_time = start_time

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, end_time):
        self._end_time = end_time

    @property
    def reagent_barcode(self):
        return self._reagent_barcode

    @reagent_barcode.setter
    def reagent_barcode(self, reagent_barcode):
        self._reagent_barcode = reagent_barcode

    @property
    def flowcell_barcode(self):
        return self._flowcell_barcode

    @flowcell_barcode.setter
    def flowcell_barcode(self, flowcell_barcode):
        self._flowcell_barcode = flowcell_barcode

    @property
    def sample_sheet_name(self):
        return self._sample_sheet_name

    @sample_sheet_name.setter
    def sample_sheet_name(self, sample_sheet_name):
        self._sample_sheet_name = sample_sheet_name

    @property
    def sequence_run_id(self):
        return self._sequence_run_id

    @sequence_run_id.setter
    def sequence_run_id(self, sequence_run_id):
        self._sequence_run_id = sequence_run_id

    @property
    def sequence_run_name(self):
        return self._sequence_run_name

    @sequence_run_name.setter
    def sequence_run_name(self, sequence_run_name):
        self._sequence_run_name = sequence_run_name

    def to_dict(self):
        result = {}

        for attr, _ in six.iteritems(self._types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (item[0], item[1].to_dict())
                        if hasattr(item[1], "to_dict")
                        else item,
                        value.items(),
                    )
                )
            else:
                result[attr] = value
        if issubclass(SequenceRunStateChange, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, SequenceRunStateChange):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
