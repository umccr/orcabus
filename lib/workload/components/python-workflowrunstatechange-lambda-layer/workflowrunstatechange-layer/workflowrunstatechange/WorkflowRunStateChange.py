# coding: utf-8
import pprint
import re  # noqa: F401
from datetime import datetime

import six
from . import Payload  # noqa: F401,E501


class WorkflowRunStateChange(object):
    _types = {
        'portalRunId': 'str',
        'timestamp': 'datetime',
        'status': 'str',
        'workflowType': 'str',
        'workflowVersion': 'str',
        'payload': 'Payload'
    }

    _attribute_map = {
        'portalRunId': 'portalRunId',
        'timestamp': 'timestamp',
        'status': 'status',
        'workflowName': 'workflowName',
        'workflowVersion': 'workflowVersion',
        'payload': 'payload'
    }

    def __init__(self, portal_run_id=None, timestamp=None, status=None, workflow_name=None, workflow_version=None, payload=None):  # noqa: E501
        self._portalRunId = None
        self._timestamp = None
        self._status = None
        self._workflowName = None
        self._workflowVersion = None
        self._payload = None
        self.discriminator = None
        self.portalRunId = portal_run_id
        self.timestamp = timestamp
        self.status = status
        self.workflowName = workflow_name
        self.workflowVersion = workflow_version
        self.payload = payload


    @property
    def portalRunId(self) -> str:
        """Get the portalRunId"""
        return self._portalRunId

    @portalRunId.setter
    def portalRunId(self, portalRunId: str):
        """Set the portalRunId"""
        self._portalRunId = portalRunId


    @property
    def timestamp(self) -> datetime:
        """Get the timestamp"""
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: datetime):
        """Set the timestamp"""
        self._timestamp = timestamp


    @property
    def status(self) -> str:
        """Get the status"""
        return self._status

    @status.setter
    def status(self, status: str):
        """Set the status"""
        self._status = status


    @property
    def workflowName(self) -> str:
        """Get the workflowName"""
        return self._workflowName

    @workflowName.setter
    def workflowName(self, workflowName: str):
        """Set the workflowName"""
        self._workflowName = workflowName


    @property
    def workflowVersion(self) -> str:
        """Get the workflowVersion"""
        return self._workflowVersion

    @workflowVersion.setter
    def workflowVersion(self, workflowVersion: str):
        """Set the workflowVersion"""
        self._workflowVersion = workflowVersion


    @property
    def payload(self) -> Payload:
        """Get the payload"""
        return self._payload

    @payload.setter
    def payload(self, payload: Payload):
        """Set the payload"""
        self._payload = payload

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
        if issubclass(WorkflowRunStateChange, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, WorkflowRunStateChange):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

