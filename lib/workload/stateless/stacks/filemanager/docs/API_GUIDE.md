# Filemanager API

The filemanager API gives access to S3 object records for all [S3 file events][s3-events] which are recorded in the database.

To start a local API server and view the OpenAPI documentation, run the following:

```sh
make start
```

This serves Swagger OpenAPI docs at `http://localhost:8000/swagger-ui` when using default settings.

## API configuration

The API has some environment variables that can be used to configure behaviour (for the presigned url route):

| Option                               | Description                                                                                                                    | Type                | Default                         |
|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|---------------------|---------------------------------|
| `FILEMANAGER_API_LINKS_URL`          | Override the URL which is used to generate pagination links. By default the `HOST` header is used to created pagination links. | URL                 | Not set                         |
| `FILEMANAGER_API_PRESIGN_LIMIT`      | The maximum file size in bytes which presigned URLs will be generated for.                                                     | Integer             | `"20971520"`                    | 
| `FILEMANAGER_API_PRESIGN_EXPIRY`     | The expiry time for presigned urls.                                                                                            | Duration in seconds | `"300"`                         |
| `FILEMANAGER_API_CORS_ALLOW_ORIGINS` | The origins to allow for CORS.                                                                                                 | List of origins     | Not set, no origins allowed     |
| `FILEMANAGER_API_CORS_ALLOW_METHODS` | The methods to allow for CORS.                                                                                                 | List of origins     | `"GET,HEAD,OPTIONS,POST,PATCH"` |
| `FILEMANAGER_API_CORS_ALLOW_HEADERS` | The headers to allow for CORS.                                                                                                 | List of origins     | `"authorization"`               |

The deployed instance of the filemanager API can be reached using the desired stage at `https://file.<stage>.umccr.org`
using the orcabus API token. To retrieve the token, run:

```sh
export TOKEN=$(aws secretsmanager get-secret-value --secret-id orcabus/token-service-jwt --output json --query SecretString | jq -r 'fromjson | .id_token')
```

## Querying records

The API is designed to have a standard set of REST routes which can be used to query for records. The API is version with a
`/api/v1` route prefix, and S3 object records can be reached under `/api/v1/s3`.

For example, to query a single record, use the `s3_object_id` in the path, which returns the JSON record:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3/0190465f-68fa-76e4-9c36-12bdf1a1571d" | jq
```

Multiple records can be reached using the same route, which returns an array of JSON records:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3" | jq
```

This route is paginated, and by default returns 1000 records from the first page in a JSON list response:

```json
{
  "links": {
    "previous": null,
    "next": "https://file.dev.umccr.org/api/v1/s3?page=1&rowsPerPage=1000"
  },
  "pagination": {
    "count": 1000,
    "page": 0,
    "rowsPerPage": 1000
  },
  "results": [
    "<first 1000 s3_object records>..."
  ]
}
```

Use the `page` and `rowsPerPage` query parameters to control the pagination:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3?page=10&rowsPerPage=50" | jq
```

The records can be filtered using the same fields from the record by naming the field in a query parameter.
For example, query all records for a certain bucket:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3?bucket=umccr-temp-dev" | jq
```

Since the filemanager database keeps a copy of all S3 events that it receives, old records for deleted objects
are also kept in the database. In order to retrieve only current objects, that is, objects that are still in S3 and
don't have an associated `Deleted` event, use the `currentState` query parameter:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3?currentState=true" | jq
```

### Attributes

The filemanager has the ability to save JSON attributes on any records. Attributes can be used to query similar to
filtering on record fields. The syntax for attribute querying uses square brackets to access nested JSON fields, similar
to the syntax defined by the [qs] npm package. Brackets should be percent-encoded in URLs.

For example, query for a previously set `portalRunId`:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "attributes[portalRunId]=202405212aecb782" \
"https://file.dev.umccr.org/api/v1/s3" | jq
```

> [!NOTE]  
> Attributes on filemanager records start empty. They need to be added to the record to query on them later.
> See [updating records](#updating-records)

As a convience, the filemanager has an attributes route that can be used to query by top-level attribute properties.
For example, the following is equivalent to the above query:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "portalRunId=202405212aecb782" \
"https://file.dev.umccr.org/api/v1/s3/attributes" | jq
```

### Wilcard matching

The API supports using wildcards to match multiple characters in a value for most field. Use `*` to match multiple characters
and `?` to match one character. Use a backslash character to match a literal `*` or `?` in the query. Another backslash can be used
to escape itself. No other escape characters are supported.

These get converted to postgres `like` queries under the hood. For example, query on a key prefix:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "key=temp_data*" \
"https://file.dev.umccr.org/api/v1/s3" | jq
```

Case-insensitive wildcard matching, which gets converted to a postgres `ilike` statement, is supported by using `caseSensitive`:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "key=temp_data*" \
"https://file.dev.umccr.org/api/v1/s3?caseSensitive=false" | jq
```

Wildcard matching is also supported on attributes, which get converted to jsonpath `like_regex` queries:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "attributes[portalRunId]=20240521*" \
"https://file.dev.umccr.org/api/v1/s3" | jq
```

## Multiple keys

The API supports querying using multiple keys with the same name. This represents an `or` condition in the SQL query, where
records are fetched if any of the keys match. For example, the following finds records where the bucket is either `bucket1`
or `bucket2`:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3?bucket[]=bucket1&bucket[]=bucket2" | jq
```

Multiple keys are also supported on attributes. For example, the following finds records where the `portalRunId` is
either `20240521aecb782` or `20240521aecb783`:
 
```sh
curl --get -H "Authorization: Bearer $TOKEN" \
--data-urlencode "attributes[portalRunId][]=20240521aecb782" \
--data-urlencode "attributes[portalRunId][]=20240521aecb783" \
"https://file.dev.umccr.org/api/v1/s3" | jq
```

Note that the extra `[]` is required in the query parameters to specify multiple keys with the same name. Specifying
multiple of the same key without `[]` results in an error. It is also an error to specify some keys with `[]` and some
without for keys with the same name.

## Updating records

As part of allowing filemanager to link and query on attributes, attributes can be updated using PATCH requests.
Each of the above endpoints and queries supports a PATCH request which can be used to update attributes on a set
of records, instead of listing records. All query parameters except pagination are supported for updates.
Attributes are update using [JSON patch][json-patch].

For example, update attributes on a single record:

```sh
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
--data '[ { "op": "add", "path": "/portalRunId", "value": "portalRunIdValue" } ]' \
"https://file.dev.umccr.org/api/v1/s3/0190465f-68fa-76e4-9c36-12bdf1a1571d" | jq
```

Or, update attributes for multiple records with the same key prefix:

```sh
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
--data '[ { "op": "add", "path": "/portalRunId", "value": "portalRunIdValue" } ]' \
"https://file.dev.umccr.org/api/v1/s3?key=*202405212aecb782*" | jq
```

## Count objects

There is an API route which counts the total number of records in the database, which supports
similar query parameters as the regular list operations.

For example, count the total records:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3/count" | jq
```

## Presigned URLs

The filemanager API can also generate presigned URLs. Presigned URLs can only be generated for objects that currently
exist in S3.

For example, generate a presigned URL for a single record:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3/presign/0190465f-68fa-76e4-9c36-12bdf1a1571d" | jq
```

Or, for multiple records, which supports the same query parameters as list operations (except `currentState` as that is implied):

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3/presign?page=10&rowsPerPage=50" | jq
```

Specify `responseContentDisposition` for either of the above routes to change the `response-content-disposition` for the
presigned `GetObject` request. This can either be `inline` or `attachment`. The default is `inline`:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3/presign?responseContentDisposition=attachment" | jq
```

## Some missing features

There are some missing features in the query API which are planned, namely:

* There is no way to compare values with `>`, `>=`, `<`, `<=`.
* There is no way to express `and` or `or` conditions in the API (except for multiple keys representing `or` conditions).

There are also some feature missing for attribute linking. For example, there is no way
to capture matching wildcard groups which can later be used in the JSON patch body.

There is also no way to POST an attribute linking rule, which can be used to update S3 records
as they are received by filemanager. See [ATTRIBUTE_LINKING.md][attribute-linking] for a discussion on some approaches
for this. The likely solution will involve merging the above wildcard matching logic with attribute rules.

## Htsget

Htsget support is enabled under the `htsget.file` subdomain, see [here] for more details. For each current object
returned by the filemanager, it can be reached via htsget by combining the key and the bucket in the query path:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://htsget-file.dev.umccr.org/reads/<filemanager_bucket>/<filemanager_key>" | jq
```

[json-patch]: https://jsonpatch.com/
[qs]: https://github.com/ljharb/qs
[s3-events]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html
[attribute-linking]: ATTRIBUTE_LINKING.md
[here]: ../../htsget/README.md