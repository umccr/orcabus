# coding: utf-8
import pprint
import re  # noqa: F401

import six
from enum import Enum

class LibraryRecord(object):


    _types = {
        'libraryId': 'str',
        'orcabusId': 'str'
    }

    _attribute_map = {
        'libraryId': 'libraryId',
        'orcabusId': 'orcabusId'
    }

    def __init__(self, libraryId=None, orcabusId=None):  # noqa: E501
        self._libraryId = None
        self._orcabusId = None
        self.discriminator = None
        self.libraryId = libraryId
        self.orcabusId = orcabusId


    @property
    def libraryId(self):

        return self._libraryId

    @libraryId.setter
    def libraryId(self, libraryId):


        self._libraryId = libraryId


    @property
    def orcabusId(self):

        return self._orcabusId

    @orcabusId.setter
    def orcabusId(self, orcabusId):


        self._orcabusId = orcabusId

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
        if issubclass(LibraryRecord, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, LibraryRecord):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

