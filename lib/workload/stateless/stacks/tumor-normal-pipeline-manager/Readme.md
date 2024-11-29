# Tumor Normal Pipeline Manager

This service wraps the ICAv2 dragen TN pipeline, stores inputs and outputs of the pipeline in a DynamoDb database.  

This service receives a READY Workflow Run State Change event for the Dragen Somatic Tumor Normal pipeline, and then launches the workflow on ICAv2.

The pipeline takes input files in any of the following formats:
  * Fastq.gz 
  * Fastq.ora
  * Bam
  * Cram

The data schema for the workflow run state change event is as follows:

```json
{
  "$schema": "httsp://json-schema.org/2020-12/schema#",
  "description": "",
  "type": "object",
  "properties": {
    "inputs": {
      "type": "object",
      "properties": {
        "enableDuplicateMarking": {
          "type": "boolean"
        },
        "enableCnvSomatic": {
          "type": "boolean"
        },
        "enableHrdSomatic": {
          "type": "boolean"
        },
        "enableSvSomatic": {
          "type": "boolean"
        },
        "cnvUseSomaticVcBaf": {
          "type": "boolean"
        },
        "outputPrefixSomatic": {
          "type": "string",
          "minLength": 1
        },
        "outputPrefixGermline": {
          "type": "string",
          "minLength": 1
        },
        "tumorFastqListRows": {
          "type": "array",
          "uniqueItems": true,
          "minItems": 1,
          "items": {
            "required": [
              "rgid",
              "rgsm",
              "rglb",
              "lane",
              "read1FileUri",
              "read2FileUri"
            ],
            "properties": {
              "rgid": {
                "type": "string",
                "minLength": 1
              },
              "rgsm": {
                "type": "string",
                "minLength": 1
              },
              "rglb": {
                "type": "string",
                "minLength": 1
              },
              "lane": {
                "type": "number"
              },
              "read1FileUri": {
                "type": "string",
                "minLength": 1
              },
              "read2FileUri": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        },
        "fastqListRows": {
          "type": "array",
          "uniqueItems": true,
          "minItems": 1,
          "items": {
            "required": [
              "rgid",
              "rgsm",
              "rglb",
              "lane",
              "read1FileUri",
              "read2FileUri"
            ],
            "properties": {
              "rgid": {
                "type": "string",
                "minLength": 1
              },
              "rgsm": {
                "type": "string",
                "minLength": 1
              },
              "rglb": {
                "type": "string",
                "minLength": 1
              },
              "lane": {
                "type": "number"
              },
              "read1FileUri": {
                "type": "string",
                "minLength": 1
              },
              "read2FileUri": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        },
        "dragenReferenceVersion": {
          "type": "string",
          "minLength": 1
        }
      },
      "required": [
        "enableDuplicateMarking",
        "enableCnvSomatic",
        "enableHrdSomatic",
        "enableSvSomatic",
        "cnvUseSomaticVcBaf",
        "outputPrefixSomatic",
        "outputPrefixGermline",
        "tumorFastqListRows",
        "fastqListRows",
        "dragenReferenceVersion"
      ]
    },
    "engineParameters": {
      "type": "object",
      "properties": {
        "outputUri": {
          "type": "string",
          "minLength": 1
        },
        "logsUri": {
          "type": "string",
          "minLength": 1
        },
        "cacheUri": {
          "type": "string",
          "minLength": 1
        },
        "projectId": {
          "type": "string",
          "minLength": 1
        }
      },
      "required": [
        "outputUri",
        "logsUri",
        "cacheUri",
        "projectId"
      ]
    },
    "tags": {
      "type": "object",
      "properties": {
        "subjectId": {
          "type": "string",
          "minLength": 1
        },
        "individualId": {
          "type": "string",
          "minLength": 1
        },
        "tumorLibraryId": {
          "type": "string",
          "minLength": 1
        },
        "normalLibraryId": {
          "type": "string",
          "minLength": 1
        },
        "tumorFastqListRowIds": {
          "type": "array",
          "items": {
            "required": [],
            "properties": {}
          }
        },
        "normalFastqListRowIds": {
          "type": "array",
          "items": {
            "required": [],
            "properties": {}
          }
        }
      },
      "required": [
        "subjectId",
        "individualId",
        "tumorLibraryId",
        "normalLibraryId",
        "tumorFastqListRowIds",
        "normalFastqListRowIds"
      ]
    }
  },
  "required": [
    "inputs",
    "engineParameters",
    "tags"
  ]
}
```

Example launch script



