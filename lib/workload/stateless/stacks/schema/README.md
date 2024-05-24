# Schema Stack

This stack create EventBridge event schemas in OrcaBus main bus event registry.

You do not need to make any code changes in this stack, in order to publish your event schema or data schema. Please follow instruction below.

## How to add event schema or data schema into registry?

- First, you should place your event schemas that your application service published into location: `docs/schemas/<data|events>/<namespace>`.
- Next, configure your event schema in [config/stacks/schema/events.ts](../../../../../config/stacks/schema/events.ts) or data schema in [config/stacks/schema/data.ts](../../../../../config/stacks/schema/data.ts).

This process should be pretty much boilerplate and, copy & paste ops. You typically replicate what other existing event schema do there; and follow up for yours.
