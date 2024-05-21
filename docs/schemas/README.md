# OrcaBus Schemas

- [OrcaBus Schemas](#orcabus-schemas)
  - [Event Schema](#event-schema)
    - [How to publish event schema into Registry?](#how-to-publish-event-schema-into-registry)
    - [Schema Registry](#schema-registry)
      - [Schema Retention](#schema-retention)
      - [Code Binding](#code-binding)
      - [Multiple Service Schemas](#multiple-service-schemas)
    - [Namespace](#namespace)
  - [Data Schemas](#data-schemas)


## Event Schema

Login to AWS dev account: `AWS Console > Amazon EventBridge > Schema Registry > Schemas > orcabus.events`

### How to publish event schema into Registry?

1. Study existing schemas within this directory.
2. Follow the structure and, add your schema into this directory; including example event message instances.
3. Register your schema into [`config/stacks/schema.ts`](../../config/stacks/schema.ts).
   - Follow the existing code structure. 
   - This is the only CDK TypeScript source file that need modifying.
   - The [schema](../../lib/workload/stateless/stacks/schema/README.md) stack should detect changes and deploy upon successful build. 
4. Make a PR with preferably only changes that contain about your event schema for clarity.

### Schema Registry

- When a service emits a message into the OrcaBus event bus:
  - It has to follow the message format contract that published in [EventBridge Schema Registry](https://www.google.com/search?q=EventBridge+schema+registry).
  - It must conform to event `source` property defined in `Namespace` section.
- A service may publish one or many event schemas into the registry as needed.
- Make event "observable". See [article](https://community.aws/content/2dhVUFPH16jZbhZfUB73aRVJ5uD/eventbridge-schema-registry-best-practices?lang=en).
- Event schema does not have to reflect 1-to-1 mapping with application backend database tables (i.e. how you store things). You may create "event transformer/mapper" layer within your code for this purpose.

#### Schema Retention

- Multiple versions of the same schema is allowed.
  - However, take note of [event schema evolution](https://www.google.com/search?q=event+schema+evolution). 
  - Introducing new `required` properties to the original schema may break downstream event subscriber. 
- A service can emit multiple "editions" of the same message with varying event schema for backward compatibility.

Example:

```
                                                           / MyDomainEntityStateChange     (original schema)
service -- emits -- same message in two schema editions --|  
                                                           \ MyNewDomainEntityStateChange  (contain breaking changes)
```

```
service -- emits -->  MyDomainEntityStateChange  (no breaking changes, support additional properties)

(Multiple versions of `MyDomainEntityStateChange` schema represent as `Version 1`, `Version 2`, ..., inside EventBridge Schema Registry)
```

#### Code Binding

- It is recommended to leverage [EventBridge Code Binding](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema-code-bindings.html) mechanism to auto-generate marshall/unmarshall ([serialisation](https://www.google.com/search?q=serialisation)) of the event schema; instead of manually parsing & validating the event message. Use of more advanced or, a better tooling fit-for-purpose is also encouraged when appropriate.
- The Slack [thread](https://umccr.slack.com/archives/C03ABJTSN7J/p1714731324414679) in `#orcabus` channel or https://github.com/umccr/orcabus/issues/257 share DX tips for starter.
- Organise auto-generated code in trackable manner within your application source tree. 

#### Multiple Service Schemas

- Multiple services may publish the same or similar schema due to similarity of their domain modelling aspect.
- The event schema discriminator is the event `source` property of the event message instance.
- Subscriber routes the message of interest from upstream service event source through [EventBridge Event Rule](https://www.google.com/search?q=eventbridge+event+rule); within application deployment CDK code.
- When your application subscribe to similar schema from multiple sources, you should use their reverse domain (Namespace) to manage schema code binding purpose.

Example:

```
orcabus.bclconvertmanager@WorkflowRunStateChange
orcabus.workflowmanager@WorkflowRunStateChange
```

```
{
  "detail-type": ["WorkflowRunStateChange"],
  "source": ["orcabus.workflowmanager"],
  "detail": {
    "status": ["SUCCEEDED"]
  }
}
```

```
{
  "detail-type": ["WorkflowRunStateChange"],
  "source": ["orcabus.bclconvertmanager"],
  "detail": {
    "status": ["SUCCEEDED"]
  }
}
```

### Namespace

Service namespaces are for filtering Event Rule purpose. This is used in event `source` property when service emits messages. It denotes where the message is originating from. The convention follows reverse domain name. We follow "compat" format of [CDK stack directory name](../../lib/workload/stateless/stacks). i.e. Removing dash character from kebab-case.

```
orcabus.sequencerunmanager
orcabus.filemanager
orcabus.metadatamanager
orcabus.workflowmanager
orcabus.bclconvertmanager
orcabus.bclconvertinteropqcmanager
orcabus.bsshicav2fastqcopymanager
orcabus.cttsov2manager
orcabus.pieriandxmanager
```

Example:

```
orcabus.sequencerunmanager@SequenceRunStateChange
orcabus.filemanager@FileStateChange
orcabus.metadatamanager@LibraryStateChange
orcabus.workflowmanager@WorkflowRunStateChange
orcabus.bclconvertmanager@WorkflowRunStateChange
orcabus.bclconvertinteropqcmanager@WorkflowRunStateChange
orcabus.cttsov2manager@WorkflowRunStateChange
```

## Data Schemas