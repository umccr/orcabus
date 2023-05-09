import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { EventBusConstruct, EventBusProps } from './stateful/eventbridge/component';
import { DatabaseConstruct, DatabaseProps } from './stateful/database/component';
import { SecurityGroupConstruct, SecurityGroupProps } from './stateful/securitygroup/component';
import { SchemaRegistryConstruct, SchemaRegistryProps } from './stateful/schemaregistry/component';

export interface OrcaBusStatefulConfig {
  schemaRegistryProps: SchemaRegistryProps;
  eventBusProps: EventBusProps;
  databaseProps: DatabaseProps;
  securityGroupProps: SecurityGroupProps;
}

export class OrcaBusStatefulStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatefulConfig) {
    super(scope, id, props);

    // --- Constructs pre-existing resources

    const vpc = getVpc(this);

    // --- Create Stateful resources

    new EventBusConstruct(this, 'OrcaBusEventBusConstruct', props.eventBusProps);
    new DatabaseConstruct(this, 'OrcaBusDatabaseConstruct', vpc, props.databaseProps);
    new SecurityGroupConstruct(
      this,
      'OrcaBusSecurityGroupConstruct',
      vpc,
      props.securityGroupProps
    );
    new SchemaRegistryConstruct(this, 'SchemaRegistryConstruct', props.schemaRegistryProps);
  }
}
