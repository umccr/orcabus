# coding: utf-8
import pprint

import six

class CaseRunStateChange(object):


    _types = {
        'portalRunId': 'str',
        'executionId': 'str',
        'timestamp': 'datetime',
        'status': 'str',
        'caseName': 'str',
        'caseVersion': 'str',
        'caseRunName': 'str',
        'linkedLibraries': 'list[LibraryRecord]',
        'payload': 'Payload'
    }

    _attribute_map = {
        'portalRunId': 'portalRunId',
        'executionId': 'executionId',
        'timestamp': 'timestamp',
        'status': 'status',
        'caseName': 'caseName',
        'caseVersion': 'caseVersion',
        'caseRunName': 'caseRunName',
        'linkedLibraries': 'linkedLibraries',
        'payload': 'payload'
    }

    def __init__(self, portalRunId=None, executionId=None, timestamp=None, status=None, caseName=None, caseVersion=None, caseRunName=None, linkedLibraries=None, payload=None):  # noqa: E501
        self._portalRunId = None
        self._executionId = None
        self._timestamp = None
        self._status = None
        self._caseName = None
        self._caseVersion = None
        self._caseRunName = None
        self._linkedLibraries = None
        self._payload = None
        self.discriminator = None
        self.portalRunId = portalRunId
        self.executionId = executionId
        self.timestamp = timestamp
        self.status = status
        self.caseName = caseName
        self.caseVersion = caseVersion
        self.caseRunName = caseRunName
        self.linkedLibraries = linkedLibraries
        self.payload = payload


    @property
    def portalRunId(self):

        return self._portalRunId

    @portalRunId.setter
    def portalRunId(self, portalRunId):


        self._portalRunId = portalRunId


    @property
    def executionId(self):

        return self._executionId

    @executionId.setter
    def executionId(self, executionId):


        self._executionId = executionId


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
    def caseName(self):

        return self._caseName

    @caseName.setter
    def caseName(self, caseName):


        self._caseName = caseName


    @property
    def caseVersion(self):

        return self._caseVersion

    @caseVersion.setter
    def caseVersion(self, caseVersion):


        self._caseVersion = caseVersion


    @property
    def caseRunName(self):

        return self._caseRunName

    @caseRunName.setter
    def caseRunName(self, caseRunName):


        self._caseRunName = caseRunName


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
        if issubclass(CaseRunStateChange, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, CaseRunStateChange):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

