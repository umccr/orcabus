# coding: utf-8
import pprint
import re  # noqa: F401

import six
from enum import Enum

class PayloadDataSucceeded(object):


    _types = {
        'projectId': 'str',
        'analysisId': 'str',
        'userReference': 'str',
        'timeCreated': 'str',
        'timeModified': 'str',
        'pipelineId': 'str',
        'pipelineCode': 'str',
        'pipelineDescription': 'str',
        'pipelineUrn': 'str',
        'instrumentRunId': 'str',
        'basespaceRunId': 'str',
        'samplesheetB64gz': 'str'
    }

    _attribute_map = {
        'projectId': 'projectId',
        'analysisId': 'analysisId',
        'userReference': 'userReference',
        'timeCreated': 'timeCreated',
        'timeModified': 'timeModified',
        'pipelineId': 'pipelineId',
        'pipelineCode': 'pipelineCode',
        'pipelineDescription': 'pipelineDescription',
        'pipelineUrn': 'pipelineUrn',
        'instrumentRunId': 'instrumentRunId',
        'basespaceRunId': 'basespaceRunId',
        'samplesheetB64gz': 'samplesheetB64gz'
    }

    def __init__(self, projectId=None, analysisId=None, userReference=None, timeCreated=None, timeModified=None, pipelineId=None, pipelineCode=None, pipelineDescription=None, pipelineUrn=None, instrumentRunId=None, basespaceRunId=None, samplesheetB64gz=None):  # noqa: E501
        self._projectId = None
        self._analysisId = None
        self._userReference = None
        self._timeCreated = None
        self._timeModified = None
        self._pipelineId = None
        self._pipelineCode = None
        self._pipelineDescription = None
        self._pipelineUrn = None
        self._instrumentRunId = None
        self._basespaceRunId = None
        self._samplesheetB64gz = None
        self.discriminator = None
        self.projectId = projectId
        self.analysisId = analysisId
        self.userReference = userReference
        self.timeCreated = timeCreated
        self.timeModified = timeModified
        self.pipelineId = pipelineId
        self.pipelineCode = pipelineCode
        self.pipelineDescription = pipelineDescription
        self.pipelineUrn = pipelineUrn
        self.instrumentRunId = instrumentRunId
        self.basespaceRunId = basespaceRunId
        self.samplesheetB64gz = samplesheetB64gz


    @property
    def projectId(self):

        return self._projectId

    @projectId.setter
    def projectId(self, projectId):


        self._projectId = projectId


    @property
    def analysisId(self):

        return self._analysisId

    @analysisId.setter
    def analysisId(self, analysisId):


        self._analysisId = analysisId


    @property
    def userReference(self):

        return self._userReference

    @userReference.setter
    def userReference(self, userReference):


        self._userReference = userReference


    @property
    def timeCreated(self):

        return self._timeCreated

    @timeCreated.setter
    def timeCreated(self, timeCreated):


        self._timeCreated = timeCreated


    @property
    def timeModified(self):

        return self._timeModified

    @timeModified.setter
    def timeModified(self, timeModified):


        self._timeModified = timeModified


    @property
    def pipelineId(self):

        return self._pipelineId

    @pipelineId.setter
    def pipelineId(self, pipelineId):


        self._pipelineId = pipelineId


    @property
    def pipelineCode(self):

        return self._pipelineCode

    @pipelineCode.setter
    def pipelineCode(self, pipelineCode):


        self._pipelineCode = pipelineCode


    @property
    def pipelineDescription(self):

        return self._pipelineDescription

    @pipelineDescription.setter
    def pipelineDescription(self, pipelineDescription):


        self._pipelineDescription = pipelineDescription


    @property
    def pipelineUrn(self):

        return self._pipelineUrn

    @pipelineUrn.setter
    def pipelineUrn(self, pipelineUrn):


        self._pipelineUrn = pipelineUrn


    @property
    def instrumentRunId(self):

        return self._instrumentRunId

    @instrumentRunId.setter
    def instrumentRunId(self, instrumentRunId):


        self._instrumentRunId = instrumentRunId


    @property
    def basespaceRunId(self):

        return self._basespaceRunId

    @basespaceRunId.setter
    def basespaceRunId(self, basespaceRunId):


        self._basespaceRunId = basespaceRunId


    @property
    def samplesheetB64gz(self):

        return self._samplesheetB64gz

    @samplesheetB64gz.setter
    def samplesheetB64gz(self, samplesheetB64gz):


        self._samplesheetB64gz = samplesheetB64gz

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
        if issubclass(PayloadDataSucceeded, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, PayloadDataSucceeded):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

