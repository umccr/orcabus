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
  readonly eventBus: EventBusConstruct;
  readonly database: DatabaseConstruct;
  readonly securityGroup: SecurityGroupConstruct;
  readonly schemaRegistry: SchemaRegistryConstruct;

  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatefulConfig) {
    super(scope, id, props);

    // --- Constructs pre-existing resources

    const vpc = getVpc(this);

    // --- Create Stateful resources

    this.eventBus = new EventBusConstruct(this, 'OrcaBusEventBusConstruct', props.eventBusProps);
    this.securityGroup = new SecurityGroupConstruct(
      this,
      'OrcaBusSecurityGroupConstruct',
      vpc,
      props.securityGroupProps
    );
    this.database = new DatabaseConstruct(this, 'OrcaBusDatabaseConstruct', vpc, {
      ...props.databaseProps,
      allowDbIngressRule: [
        { peer: this.securityGroup.lambdaSecurityGroup, description: 'allow lambda SecurityGroup' },
      ],
    });
    this.schemaRegistry = new SchemaRegistryConstruct(
      this,
      'SchemaRegistryConstruct',
      props.schemaRegistryProps
    );
  }
}
