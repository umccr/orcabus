import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { EventBusConstruct } from './stateful/eventbridge/component';
import { DatabaseConstruct } from './stateful/database/component';
import { SecurityGroupConstruct } from './stateful/securitygroup/component';
import { SchemaRegistryConstruct, Props as SchemaRegistryProps } from './stateful/schemaregistry/component';

export interface OrcaBusStatefulConfig {
  schemaRegistryProps: SchemaRegistryProps,
}

export class OrcaBusStatefulStack extends cdk.Stack {

  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatefulConfig) {
    super(scope, id, props);

    // --- Constructs pre-existing resources

    const vpc = getVpc(this);

    // --- Create Stateful resources

    new EventBusConstruct(this, 'OrcaBusEventBusConstruct');
    new DatabaseConstruct(this, 'OrcaBusDatabaseConstruct', { vpc: vpc });
    new SecurityGroupConstruct(this, 'OrcaBusSecurityGroupConstruct', { vpc: vpc });
    new SchemaRegistryConstruct(this, 'SchemaRegistryConstruct', props.schemaRegistryProps)
  }
}
