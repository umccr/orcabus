# Filemanager API

The filemanager API gives access to S3 object records for all [S3 file events][s3-events] which are recorded in the database.

To start a local API server and view the OpenAPI documentation, run the following:

```sh
make api
```

This serves Swagger OpenAPI docs at `http://localhost:8000/swagger_ui` when using default settings.

The deployed instance of the filemanager API can be reached using the desired stage at `https://file.<stage>.umccr.org`
using the orcabus API token. To retrieve the token, run:

```sh
export TOKEN=$(aws secretsmanager get-secret-value --secret-id orcabus/token-service-jwt --output json --query SecretString | jq -r 'fromjson | .id_token')
```

## Querying records

The API is designed to have a standard set of REST routes which can be used to query for records. The API is version with a
`/api/v1` route prefix, and S3 object records can be reached under `/api/v1/s3_objects`.

For example, to query a single record, use the `s3_object_id` in the path, which returns the JSON record:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3_objects/0190465f-68fa-76e4-9c36-12bdf1a1571d" | jq
```

Multiple records can be reached using the same route, which returns an array of JSON records:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3_objects" | jq
```

This route is paginated, and by default returns 1000 records from the first page in a JSON list response:

```json
{
  "next_page": 1,
  "results": [
    "<first 1000 s3_object records>..."
  ]
}
```

Use the `page` and `page_size` query parameters to control the pagination:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3_objects?page=10&page_size=50" | jq
```

The records can be filtered using the same fields from the record by naming the field in a query parameter.
For example, query all records for a certain bucket:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3_objects?bucket=umccr-temp-dev" | jq
```

Since the filemanager database keeps a copy of all S3 events that it receives, old records for deleted objects
are also kept in the database. In order to retrieve only current objects, that is, objects that are still in S3 and
don't have an associated `Deleted` event, use the `current_state` query parameter:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3_objects?current_state=true" | jq
```

### Attributes

The filemanager has the ability to save JSON attributes on any records. Attributes can be used to query similar to
filtering on record fields. The syntax for attribute querying uses square brackets to access nested JSON fields, similar
to the syntax defined by the [qs] npm package. Brackets should be percent-encoded in URLs.

For example, query for a previously set `portal_run_id`:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "attributes[portal_run_id]=202405212aecb782" \
"https://file.dev.umccr.org/api/v1/s3_objects" | jq
```

> [!NOTE]  
> Attributes on filemanager records start empty. They need to be added to the record to query on them later.
> See [updating records](#updating-records)

### Wilcard matching

The API supports using wildcards to match multiple characters in a value for most field. Use `%` to match multiple characters
and `_` to match one character. These queries get converted to postgres `like` queries under the hood. For example, query
on a key prefix:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "key=temp\_data%" \
"https://file.dev.umccr.org/api/v1/s3_objects" | jq
```

Case-insensitive wildcard matching, which gets converted to a postgres `ilike` statement, is supported by using `case_sensitive`:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "key=temp\_data%" \
"https://file.dev.umccr.org/api/v1/s3_objects?case_sensitive=false" | jq
```

Wildcard matching is also supported on attributes:

```sh
curl --get -H "Authorization: Bearer $TOKEN" --data-urlencode "attributes[portal_run_id]=20240521%" \
"https://file.dev.umccr.org/api/v1/s3_objects" | jq
```

## Updating records

As part of allowing filemanager to link and query on attributes, attributes can be updated using PATCH requests.
Each of the above endpoints and queries supports a PATCH request which can be used to update attributes on a set
of records, instead of listing records. All query parameters except pagination are supported for updates.
Attributes are update using [JSON patch][json-patch].

For example, update attributes on a single record:

```sh
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
--data '{ "attributes": [ { "op": "add", "path": "/portal_run_id", "value": "202405212aecb782" } ] }' \
"https://file.dev.umccr.org/api/v1/s3_objects/0190465f-68fa-76e4-9c36-12bdf1a1571d" | jq
```

Or, update attributes for multiple records with the same key prefix:

```sh
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
--data '{ "attributes": [ { "op": "add", "path": "/portal_run_id", "value": "202405212aecb782" } ] }' \
"https://file.dev.umccr.org/api/v1/s3_objects?key=%25202405212aecb782%25" | jq
```

## Count objects

There is an API route which counts the total number of records in the database, which supports
similar query parameters as the regular list operations.

For example, count the total records:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://file.dev.umccr.org/api/v1/s3_objects/count" | jq
```

## Some missing features

There are some missing features in the query API which are planned, namely:

* There is no way to compare values with `>`, `>=`, `<`, `<=`.
* There is no way to express `and` or `or` conditions in the API.

There are also some feature missing for attribute linking. For example, there is no way
to capture matching wildcard groups which can later be used in the JSON patch body.

There is also no way to POST an attribute linking rule, which can be used to update S3 records
as they are received by filemanager. See [ATTRIBUTE_LINKING.md][attribute-linking] for a discussion on some approaches
for this. The likely solution will involve merging the above wildcard matching logic with attribute rules.

[json-patch]: https://jsonpatch.com/
[qs]: https://github.com/ljharb/qs
[s3-events]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html
[attribute-linking]: ATTRIBUTE_LINKING.md