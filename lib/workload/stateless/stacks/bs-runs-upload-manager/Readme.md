# BS Runs Upload Manager

<!-- TOC -->
* [BS Runs Upload Manager](#bs-runs-upload-manager)
  * [Summary](#summary)
  * [Inputs](#inputs)
    * [Example input](#example-input)
    * [Lambdas in this directory](#lambdas-in-this-directory)
      * [Upload V2 SampleSheet to GDS Bssh](#upload-v2-samplesheet-to-gds-bssh)
      * [Launch BS Runs Upload Tes](#launch-bs-runs-upload-tes)
<!-- TOC -->

## Summary

Quick and dirty hack to push our runs from ICAv1 to our V2 BaseSpace server domain

Once we move from V1 to V2 we probably won't need this.  

This statemachine will copy data from v1 to v2 via bs runs upload.  

The bs runs upload will trigger an Autolaunch of BCLConvert in ICAv2.

The two steps of the statemachine are:

1. Generate a V2 Samplesheet and reupload it
2. Launch an ICAv1 tes task that runs the bs runs upload command

This statemachine will subscribe to the orcabus.srm events and trigger the statemachine when a new run is detected.

![](images/bs_runs_upload_manager.png)

## Inputs

The AWS Step functions takes in the following parameters

* runFolderPath: The path to the run folder in GDS
* runVolumeName: The GDS volume name
* sampleSheetName: The name of the sample sheet file

### Example input

```json
{
  "runFolderPath": "/Runs/231109_A01052_0171_BHLJW7DSX7_r.NULhvzxcSEWmqZw8QljXfQ",
  "runVolumeName": "bssh.acddbfda498038ed99fa94fe79523959",
  "sampleSheetName": "SampleSheet.csv"
}
```

### Lambdas in this directory

#### Upload V2 SampleSheet to GDS Bssh

This lambda will take in an existing v1 samplesheet and convert it to a v2 samplesheet.  It will then upload the v2 samplesheet to the GDS volume.

This uses the ssbackend API in order to generate the V2 samplesheet since some metadata is required to create V2 samplesheets not present in the V1 samplesheet.

**Example Input**

```json
{
  "gds_folder_path": "/Runs/240315_A01052_0186_AH5HM5DSXC_r.YpC_0U_7-06Oom1cFl9Y5A",
  "gds_volume_name": "bssh.acddbfda498038ed99fa94fe79523959",
  "samplesheet_name": "SampleSheet.csv"
}
```

**Example Output**

```json
{
  "gds_folder_path": "/Runs/240315_A01052_0186_AH5HM5DSXC_r.YpC_0U_7-06Oom1cFl9Y5A",
  "gds_volume_name": "bssh.acddbfda498038ed99fa94fe79523959",
  "samplesheet_name": "SampleSheet.V2.<timestamp>.csv",
  "instrument_run_id": "240315_A01052_0186_AH5HM5DSXC"
}
```

#### Launch BS Runs Upload Tes

This lambda will launch a tes task that will run the bs runs upload command.

**Example Input**

```json
{
  "gds_folder_path": "/Runs/240315_A01052_0186_AH5HM5DSXC_r.YpC_0U_7-06Oom1cFl9Y5A",
  "gds_volume_name": "bssh.acddbfda498038ed99fa94fe79523959",
  "samplesheet_name": "SampleSheet.V2.<timestamp>.csv",
  "instrument_run_id": "240315_A01052_0186_AH5HM5DSXC"
}
```

**Example Output**

```json
{
  "task_run_id": "trn.4fd3414f98fe47c3a6cfc31a67b7418a"
}
```

#### External parameters

The following properites are required in order to deploy the statemachine / stack:

* SecretsManager: 
  * ICA Access Token: `IcaSecretsPortal`
  * Portal Token: `orcabus/token-service-jwt`
  * BaseSpace Token Secret ID: `/manual/BaseSpaceAccessTokenSecret`
* Strings
  * gds system files path root (where to do the TES logs go?)
  * EventBus Name: `OrcabusMain`