# coding: utf-8
import pprint
import re  # noqa: F401

import six
from enum import Enum
from workflowrunstatechange.Data import Data  # noqa: F401,E501

class Payload(object):


    _types = {
        'refId': 'str',
        'version': 'str',
        'data': 'Data'
    }

    _attribute_map = {
        'refId': 'refId',
        'version': 'version',
        'data': 'data'
    }

    def __init__(self, refId=None, version=None, data=None):  # noqa: E501
        self._refId = None
        self._version = None
        self._data = None
        self.discriminator = None
        self.refId = refId
        self.version = version
        self.data = data


    @property
    def refId(self):

        return self._refId

    @refId.setter
    def refId(self, refId):


        self._refId = refId


    @property
    def version(self):

        return self._version

    @version.setter
    def version(self, version):


        self._version = version


    @property
    def data(self):

        return self._data

    @data.setter
    def data(self, data):


        self._data = data

    def to_dict(self):
        result = {}

        for attr, _ in six.iteritems(self._types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(Payload, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, Payload):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

