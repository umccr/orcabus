# coding: utf-8
import pprint
import re  # noqa: F401

import six
from enum import Enum

class MetadataStateChange(object):


    _types = {
        'action': 'str',
        'data': 'object',
        'model': 'str',
        'refId': 'str'
    }

    _attribute_map = {
        'action': 'action',
        'data': 'data',
        'model': 'model',
        'refId': 'refId'
    }

    def __init__(self, action=None, data=None, model=None, refId=None):  # noqa: E501
        self._action = None
        self._data = None
        self._model = None
        self._refId = None
        self.discriminator = None
        self.action = action
        self.data = data
        self.model = model
        self.refId = refId


    @property
    def action(self):

        return self._action

    @action.setter
    def action(self, action):


        self._action = action


    @property
    def data(self):

        return self._data

    @data.setter
    def data(self, data):


        self._data = data


    @property
    def model(self):

        return self._model

    @model.setter
    def model(self, model):


        self._model = model


    @property
    def refId(self):

        return self._refId

    @refId.setter
    def refId(self, refId):


        self._refId = refId

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
        if issubclass(MetadataStateChange, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, MetadataStateChange):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

