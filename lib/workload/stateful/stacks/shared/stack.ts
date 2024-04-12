import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { EventBusConstruct, EventBusProps } from './constructs/event-bus';
import { ConfigurableDatabaseProps, DatabaseConstruct } from './constructs/database';
import { ComputeProps, ComputeConstruct } from './constructs/compute';
import { SchemaRegistryConstruct, SchemaRegistryProps } from './constructs/schema-registry';
import { EventSourceConstruct, EventSourceProps } from './constructs/event-source';

export interface SharedStackProps {
  /**
   * Any configuration related to the SchemaRegistryConstruct
   */
  schemaRegistryProps: SchemaRegistryProps;
  /**
   * Any configuration related to the EventBusConstruct
   */
  eventBusProps: EventBusProps;
  /**
   * Any configuration related to database
   */
  databaseProps: ConfigurableDatabaseProps;
  /**
   * Any configuration related to shared compute resources
   */
  computeProps: ComputeProps;
  /**
   * Any configuration related to event source
   */
  eventSourceProps?: EventSourceProps;
  /**
   * VPC (lookup props) that will be used by resources
   */
  vpcProps: VpcLookupOptions;
}

export class SharedStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & SharedStackProps) {
    super(scope, id, props);

    const mainVpc = Vpc.fromLookup(scope, 'MainVpc', props.vpcProps);

    const computeResources = new ComputeConstruct(
      this,
      'ComputeConstruct',
      mainVpc,
      props.computeProps
    );

    new EventBusConstruct(this, 'EventBusConstruct', props.eventBusProps);

    new DatabaseConstruct(this, 'DatabaseConstruct', {
      vpc: mainVpc,
      allowedInboundSG: computeResources.securityGroup,
      ...props.databaseProps,
    });

    new SchemaRegistryConstruct(this, 'SchemaRegistryConstruct', props.schemaRegistryProps);

    if (props.eventSourceProps) {
      new EventSourceConstruct(this, 'EventSourceConstruct', props.eventSourceProps);
    }
  }
}
