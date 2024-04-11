import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { EventBusConstruct, EventBusProps } from './constructs/eventbridge';
import { ConfigurableDatabaseProps, Database } from './constructs/database';
import { ComputeConfig, ComputeConstruct } from './constructs/compute';
import { SchemaRegistryConstruct, SchemaRegistryProps } from './constructs/schemaregistry';
import { EventSource, EventSourceProps } from './constructs/event-source';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { getVpc } from '../../../components/vpc';

export interface SharedStackProps {
  schemaRegistryProps: SchemaRegistryProps;
  eventBusProps: EventBusProps;
  databaseProps: ConfigurableDatabaseProps;
  computeConfig: ComputeConfig;
  eventSourceProps?: EventSourceProps;
}


export class SharedStack extends Stack {
  constructor(
    scope: Construct,
    id: string,
    props: StackProps & SharedStackProps
  ) {
    super(scope, id, props);

    const mainVpc = getVpc(this)

    const computeResources = new ComputeConstruct(
      this,
      'ComputeConstruct',
      mainVpc,
      props.computeConfig
    );

    new EventBusConstruct(this, 'OrcaBusEventBusConstruct', props.eventBusProps);

    new Database(this, 'OrcaBusDatabaseConstruct', {
      vpc: mainVpc,
      allowedInboundSG: computeResources.securityGroup,
      ...props.databaseProps,
    });

    new SchemaRegistryConstruct(this, 'SchemaRegistryConstruct', props.schemaRegistryProps);

    if (props.eventSourceProps) {
      new EventSource(this, 'EventSourceConstruct', props.eventSourceProps);
    }
  }
}
