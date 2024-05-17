# coding: utf-8
import pprint
import re  # noqa: F401
from datetime import datetime
from typing import List

import six
from workflowrunstatechange.WorkflowRunStateChange import WorkflowRunStateChange  # noqa: F401,E501


class AWSEvent(object):
    _types = {
        'detail': 'WorkflowRunStateChange',
        'account': 'str',
        'detail_type': 'str',
        'id': 'str',
        'region': 'str',
        'resources': 'list[str]',
        'source': 'str',
        'time': 'datetime',
        'version': 'str'
    }

    _attribute_map = {
        'detail': 'detail',
        'account': 'account',
        'detail_type': 'detail-type',
        'id': 'id',
        'region': 'region',
        'resources': 'resources',
        'source': 'source',
        'time': 'time',
        'version': 'version'
    }

    def __init__(
        self, detail=None, account=None, detail_type=None,
        id=None, region=None, resources=None, source=None,
        time=None, version=None
    ):  # noqa: E501
        self._detail = None
        self._account = None
        self._detail_type = None
        self._id = None
        self._region = None
        self._resources = None
        self._source = None
        self._time = None
        self._version = None
        self.discriminator = None
        self.detail = detail
        self.account = account
        self.detail_type = detail_type
        self.id = id
        self.region = region
        self.resources = resources
        self.source = source
        self.time = time
        self.version = version

    @property
    def detail(self) -> WorkflowRunStateChange:
        """Get Detail"""
        return self._detail

    @detail.setter
    def detail(self, detail: WorkflowRunStateChange):
        """Set detail"""
        self._detail = detail

    @property
    def account(self) -> str:
        """Get account"""
        return self._account

    @account.setter
    def account(self, account: str):
        """Set account"""
        self._account = account

    @property
    def detail_type(self) -> str:
        """Get detail type"""
        return self._detail_type

    @detail_type.setter
    def detail_type(self, detail_type: str):
        """Set detail type"""
        self._detail_type = detail_type

    @property
    def id(self) -> str:
        """Get ID"""
        return self._id

    @id.setter
    def id(self, _id: str):
        """Set ID"""
        self._id = _id

    @property
    def region(self) -> str:
        """Get Region"""
        return self._region

    @region.setter
    def region(self, region: str):
        """Set Region"""
        self._region = region

    @property
    def resources(self) -> str:
        """Get Resources"""
        return self._resources

    @resources.setter
    def resources(self, resources: List[str]):
        """Set Resources"""
        self._resources = resources

    @property
    def source(self) -> str:
        """Get source"""
        return self._source

    @source.setter
    def source(self, source: str):
        """Set source"""
        self._source = source

    @property
    def time(self) -> datetime:
        """Get timestamp"""
        return self._time

    @time.setter
    def time(self, time: datetime):
        """Set timestamp"""
        self._time = time

    @property
    def version(self) -> str:
        """Get Version"""
        return self._version

    @version.setter
    def version(self, version: str):
        """Set Version"""
        self._version = version

    def to_dict(self):
        """Write AWS Event to dict"""
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
        if issubclass(AWSEvent, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self) -> str:
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, AWSEvent):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        x = dict({})
        return not self == other
