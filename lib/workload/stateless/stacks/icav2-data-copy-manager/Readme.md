# ICAv2 Data Copy Manager

Service for copying data from one location to another.  

Supports a TaskToken object that can be used to allow step functions to hang until the copy is complete for other services
that may call this service.

## Usage

Given a list of source uris, and a destination uri, the service will copy the data from the source to the destination.

The destination uri does not need to exist prior to the copy, but the source uris must exist.

**If the source uri is a folder, it will be a subfolder in the destination.**

If a file size is a single-part-upload, we will use the `requests` library to download the file and upload it to the destination,
since single-part uploads often fail when the source object is tagged.  

AWS S3 URIs in the sourceUriList and destinationUri are also supported.

The Task Token is optional and can be used to allow the calling service to wait for the copy to complete.

## Event Example

```json
{
  "EventBusName": "OrcaBusMain",
  "Source": "Whatever",
  "DetailType": "ICAv2DataCopySync",
  "Detail": {
    "payload": {
      "sourceUriList": [
        "icav2://project-id-or-name/path-to-data.txt",
        "icav2://project-id-or-name/path-to-folder/"
      ],
      "destinationUri": "icav2://project-id-or-name/path-to-destination/"
    },
    "taskToken": "your-task-token"
  }
}
```

## Recursive Copy

This service will recursively copy all files and folders from the source to the destination. 
For each subfolder, it will generate its own copy event and send it to the event bus, which is picked up by itself.  

This allows for a single event to be sent to the service, and it will handle the rest. 

Be very careful with this, recursive events should be used with caution, as they can cause infinite loops if not handled properly.
