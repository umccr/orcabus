# FileManager Attribute Linking

The filemanager needs to be able to store data from other microservices on `s3_object` records in order to perform some
logic, e.g. querying on the stored data. Ideally the filemanager should only deal with object records, without having
to know the domain of other microservices. This means that the filemanager needs a mechanism to store arbitrary
data, and be told what data to store for a given record.

## Storing attributes

The first part of the problem, i.e. storing data on records is solved by using the `attributes` column on `s3_object`.
The `attributes` can store arbitrary JSON data, which can be queried for using postgres JSON extensions.
E.g. To fetch all objects where the attributes contain an 'attribute_id' looks like:

```sql
select * from s3_object where attributes @> '{ "attribute_id": "some_id" }';
```

From the API a nested style syntax can be used:

```
/api/v1/s3_objects?attributes[attribute_id]=some_id
```

Attributes can be used by other services to perform logic, e.g. the UI could fetch all objects where
the `portal_run_id` equals `<some_id>`.

## Knowing what attributes to store

The filemanager needs to be told by other services what attributes to store. However, it only receives native S3 events
as input which cannot be edited.

A generalisable way to accomplish this is to allow the filemanager to accept a set of 'rules', which given
an S3 event as input, determine the attribute. For example, a rule could be:

* For all events where the bucket equals 'umccr-temp-dev', and the key starts with a prefix 'analysis_data/.../.../.../...'
extract the 4th path segment and add the attribute: `{ "portal_run_id": "<4th path segment>" }`.

### Rules engine

The microservice which knows about the rule could tell the filemanager about it. The rules could be published on the
event bus and use a JSON rules engine, similar to the way EventBridge rules are parsed.

For example, the workflow manager could tell filemanager a rule about matching buckets/keys using the following event message:

```json
{
  "detail-type": [
    "FileManagerAttributeRule"
  ],
  "source": [
    "orcabus.workflowmanager"
  ],
  "detail": {
    "rule": {
      "bucket": "umccr-temp-dev",
      "key": "some_prefix/(*)/*"
    },
    "apply": {
      "some_attribute_id": "<first_wildcard_capture_group>"
    },
    "start_from": "<apply_to_events_after_this_date>",
    "expires": "<date_where_rule_no_longer_applies>"
  }
}
```

This rule would match all S3 events that have 'umccr-temp-dev' as the bucket, and keys with 'some_prefix' containing a 
regex capture group. The rule only applies to events received between `starts_from` and `expires`.

Filemanager would store this rule, and check existing rules for each S3 event to see if it needs to add
attributes. If the rule is received by filemanager after an event has already fired, that's okay, the filemanager can
apply the rule retroactively to its database records.

The advantage of this approach is that it is quite general, and it means that the filemanager doesn't need to know any
details about other microservices' logic/domains. Rules also don't need to be emitted by services to be used. For example,
statically derived attributes that only need information from the S3 event could be initialized into the filemanager
database as it's deployed.

Rules could be updated if required. There could also be different operators that merge attributes in different ways,
e.g. 'append attribute', 'append if not exists', 'update attribute', 'overwrite attribute', etc.

A potential disadvantage is that the rules engine may not be flexible enough to accommodate all attribute requirements.
E.g. it's not possible to execute arbitrary code to compute the attribute.

### Technical challenges

It doesn't seem like there are many implementations of JSON rules engines. In Rust there is [json-rules-engine-rs],
which seems to be based on the javascript [json-rules-engine]. Notably, there is 
[Event Ruler][aws-event-ruler] which is a Java library and what AWS EventBridge rules uses. Calling a Java library
from Rust would require some FFI bindings.

An existing library doesn't have to be used. Since the format of S3 events is known in advance, 
a simpler approach would probably involve implementing the rules manually in filemanager, leveraging something like [serde_json].

[json-rules-engine-rs]: https://github.com/GopherJ/json-rules-engine-rs
[json-rules-engine]: https://github.com/CacheControl/json-rules-engine
[aws-event-ruler]: https://github.com/aws/event-ruler
[serde_json]: https://github.com/serde-rs/json

### Architecture

The architecture of this approach could look something like this, where each service emits rules for the filemanager to
consume:

![filemanager_attribute_linking](./filemanager_attributes.drawio.svg)

Here the filemanager stores rules in its database and processes them directly.

Alternatively, the linking logic could be a separate microservice (FileManagerAttributeManager? ThePreFileManagerManager?):

![filemanager_attribute_linking_service](./filemanager_attributes_alt.drawio.svg)

Here the filemanager ingests events that contain additional attributes from another SQS queue, and the
attribute manager consumes events from the S3 queue. In order to update existing records, the filemanager could
accept a POST request to update a set of records that the attribute manager knows about.

An advantage of this approach is that it can use different languages, which would be useful if using rules libraries like
Event Ruler.

The disadvantage is that it adds more complexity, and more latency in the S3 event processing, because now
the filemanager is no longer directly consuming S3 events.

## Alternatives

Instead of microservices pushing rules into the event bus, the filemanager could query the microservices to decide what
to do with the events. However, this adds many API calls if the filemanager has to query on a per-event basis.

Instead of reading/parsing rules in JSON, there could be a filemanager extension/plugin system which runs on each S3
event to determine attributes. This could be separate from the filemanager code, and would work well for
statically derived attributes. However, it may also introduce many API calls if the filemanager has to query other microservices
on a per-event basis.

A combination of these approaches is also possible, where there is some rule matching, and an extension which can 
query other microservices/perform complex logic on the matched events only.

## Questions

1. Is a rule-based regex-style approach enough to cover all use-cases for generating attributes, or does more complicated
   logic need to happen?
2. Are expiry/start dates for rules flexible enough to deal with changes in the rules over time?

