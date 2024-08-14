# coding: utf-8
import pprint

import six

class WorkflowRunStateChange(object):


    _types = {
        'portalRunId': 'str',
        'timestamp': 'datetime',
        'status': 'str',
        'workflowName': 'str',
        'workflowVersion': 'str',
        'workflowRunName': 'str',
        'linkedLibraries': 'list[str]',
        'payload': 'Payload'
    }

    _attribute_map = {
        'portalRunId': 'portalRunId',
        'timestamp': 'timestamp',
        'status': 'status',
        'workflowName': 'workflowName',
        'workflowVersion': 'workflowVersion',
        'workflowRunName': 'workflowRunName',
        'linkedLibraries': 'linkedLibraries',
        'payload': 'payload'
    }

    def __init__(self, portalRunId=None, timestamp=None, status=None, workflowName=None, workflowVersion=None, workflowRunName=None, linkedLibraries=None, payload=None):  # noqa: E501
        self._portalRunId = None
        self._timestamp = None
        self._status = None
        self._workflowName = None
        self._workflowVersion = None
        self._workflowRunName = None
        self._linkedLibraries = None
        self._payload = None
        self.discriminator = None
        self.portalRunId = portalRunId
        self.timestamp = timestamp
        self.status = status
        self.workflowName = workflowName
        self.workflowVersion = workflowVersion
        self.workflowRunName = workflowRunName
        self.linkedLibraries = linkedLibraries
        self.payload = payload


    @property
    def portalRunId(self):

        return self._portalRunId

    @portalRunId.setter
    def portalRunId(self, portalRunId):


        self._portalRunId = portalRunId


    @property
    def timestamp(self):

        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):


        self._timestamp = timestamp


    @property
    def status(self):

        return self._status

    @status.setter
    def status(self, status):


        self._status = status


    @property
    def workflowName(self):

        return self._workflowName

    @workflowName.setter
    def workflowName(self, workflowName):


        self._workflowName = workflowName


    @property
    def workflowVersion(self):

        return self._workflowVersion

    @workflowVersion.setter
    def workflowVersion(self, workflowVersion):


        self._workflowVersion = workflowVersion


    @property
    def workflowRunName(self):

        return self._workflowRunName

    @workflowRunName.setter
    def workflowRunName(self, workflowRunName):


        self._workflowRunName = workflowRunName

 
    @property
    def linkedLibraries(self):

        return self._linkedLibraries

    @linkedLibraries.setter
    def linkedLibraries(self, linkedLibraries):


        self._linkedLibraries = linkedLibraries


    @property
    def payload(self):

        return self._payload

    @payload.setter
    def payload(self, payload):


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

