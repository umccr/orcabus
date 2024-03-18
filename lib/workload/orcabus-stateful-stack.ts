import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { EventBusConstruct, EventBusProps } from './stateful/eventbridge/component';
import { ConfigurableDatabaseProps, Database } from './stateful/database/component';
import { SecurityGroupConstruct, SecurityGroupProps } from './stateful/securitygroup/component';
import { SchemaRegistryConstruct, SchemaRegistryProps } from './stateful/schemaregistry/component';
import { EventSource, EventSourceProps } from './stateful/event_source/component';

export interface OrcaBusStatefulConfig {
  schemaRegistryProps: SchemaRegistryProps;
  eventBusProps: EventBusProps;
  databaseProps: ConfigurableDatabaseProps;
  securityGroupProps: SecurityGroupProps;
  eventSourceProps?: EventSourceProps;
}

export class OrcaBusStatefulStack extends cdk.Stack {
  readonly eventBus: EventBusConstruct;
  readonly database: Database;
  readonly securityGroup: SecurityGroupConstruct;
  readonly schemaRegistry: SchemaRegistryConstruct;
  readonly eventSource?: EventSource;

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

    this.database = new Database(this, 'OrcaBusDatabaseConstruct', {
      vpc,
      allowedInboundSG: this.securityGroup.computeSecurityGroup,
      ...props.databaseProps,
    });

    this.schemaRegistry = new SchemaRegistryConstruct(
      this,
      'SchemaRegistryConstruct',
      props.schemaRegistryProps
    );

    if (props.eventSourceProps) {
      this.eventSource = new EventSource(this, 'EventSourceConstruct', props.eventSourceProps);
    }
  }
}
