# filemanager-api-lambda

This is a Lambda function integrated with API Gateway to respond to requests in the same way as [`filemanager-api-server`][filemanager-api-server].
The API Gateway endpoint is authorized via the OrcaBus bearer token. To access the endpoint, authorize the request with
the relevant token:

```sh
curl -H "Authorization: Bearer $orcabus_api_token" https://file.<stage>.umccr.org/api/v1/s3/count
```

View the [API_GUIDE.md][api-guide] for more information about the filemanager API.

[api-guide]: ../docs/API_GUIDE.md
[filemanager-api-server]: ../filemanager-api-server
