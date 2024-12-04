# coding: utf-8
import pprint
import re  # noqa: F401

import six


class SequenceRunStateChange(object):
    _types = {
        'endTime': 'Object',
        'id': 'str',
        'instrumentRunId': 'str',
        'runDataUri': 'str',
        'runFolderPath': 'str',
        'runVolumeName': 'str',
        'sampleSheetName': 'str',
        'startTime': 'datetime',
        'status': 'str'
    }

    _attribute_map = {
        'endTime': 'endTime',
        'id': 'id',
        'instrumentRunId': 'instrumentRunId',
        'runDataUri': 'runDataUri',
        'runFolderPath': 'runFolderPath',
        'runVolumeName': 'runVolumeName',
        'sampleSheetName': 'sampleSheetName',
        'startTime': 'startTime',
        'status': 'status'
    }

    def __init__(self, endTime=None, id=None, instrumentRunId=None, runDataUri=None, runFolderPath=None, runVolumeName=None, sampleSheetName=None, startTime=None, status=None):  # noqa: E501
        self._endTime = None
        self._id = None
        self._instrumentRunId = None
        self._runDataUri = None
        self._runFolderPath = None
        self._runVolumeName = None
        self._sampleSheetName = None
        self._startTime = None
        self._status = None
        self.discriminator = None
        self.endTime = endTime
        self.id = id
        self.instrumentRunId = instrumentRunId
        self.runDataUri = runDataUri
        self.runFolderPath = runFolderPath
        self.runVolumeName = runVolumeName
        self.sampleSheetName = sampleSheetName
        self.startTime = startTime
        self.status = status


    @property
    def endTime(self):

        return self._endTime

    @endTime.setter
    def endTime(self, endTime):


        self._endTime = endTime


    @property
    def id(self):

        return self._id

    @id.setter
    def id(self, id):


        self._id = id


    @property
    def instrumentRunId(self):

        return self._instrumentRunId

    @instrumentRunId.setter
    def instrumentRunId(self, instrumentRunId):


        self._instrumentRunId = instrumentRunId


    @property
    def runDataUri(self):

        return self._runDataUri

    @runDataUri.setter
    def runDataUri(self, runDataUri):


        self._runDataUri = runDataUri


    @property
    def runFolderPath(self):

        return self._runFolderPath

    @runFolderPath.setter
    def runFolderPath(self, runFolderPath):


        self._runFolderPath = runFolderPath


    @property
    def runVolumeName(self):

        return self._runVolumeName

    @runVolumeName.setter
    def runVolumeName(self, runVolumeName):


        self._runVolumeName = runVolumeName


    @property
    def sampleSheetName(self):

        return self._sampleSheetName

    @sampleSheetName.setter
    def sampleSheetName(self, sampleSheetName):


        self._sampleSheetName = sampleSheetName


    @property
    def startTime(self):

        return self._startTime

    @startTime.setter
    def startTime(self, startTime):


        self._startTime = startTime


    @property
    def status(self):

        return self._status

    @status.setter
    def status(self, status):


        self._status = status

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

