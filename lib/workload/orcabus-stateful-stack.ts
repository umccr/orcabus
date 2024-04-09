import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { EventBusConstruct, EventBusProps } from './stateful/eventbridge/component';
import { ConfigurableDatabaseProps, Database } from './stateful/database/component';
import { SecurityGroupConstruct, SecurityGroupProps } from './stateful/securitygroup/component';
import { SchemaRegistryConstruct, SchemaRegistryProps } from './stateful/schemaregistry/component';
import { EventSource, EventSourceProps } from './stateful/event_source/component';
import { IcaEventPipeStack, IcaEventPipeStackProps } from './stateful/ica_event_pipe/stack';
import { TokenServiceProps, TokenServiceStack } from './stateful/token_service/deploy/stack';

export interface OrcaBusStatefulConfig {
  schemaRegistryProps: SchemaRegistryProps;
  eventBusProps: EventBusProps;
  databaseProps: ConfigurableDatabaseProps;
  securityGroupProps: SecurityGroupProps;
  eventSourceProps?: EventSourceProps;
  icaEventPipeProps: IcaEventPipeStackProps;
  tokenServiceProps: TokenServiceProps;
}

export class OrcaBusStatefulStack extends cdk.Stack {
  // readonly eventBus: EventBusConstruct;
  // readonly database: Database;
  // readonly securityGroup: SecurityGroupConstruct;
  // readonly schemaRegistry: SchemaRegistryConstruct;
  // readonly eventSource?: EventSource;

  // stateful stacks
  statefulStackArray: cdk.Stack[] = [];

  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatefulConfig) {
    super(scope, id, props);

    // --- Constructs pre-existing resources

    const vpc = getVpc(this);

    // --- Create Stateful resources

    new EventBusConstruct(this, 'OrcaBusEventBusConstruct', props.eventBusProps);

    const securityGroup = new SecurityGroupConstruct(
      this,
      'OrcaBusSecurityGroupConstruct',
      vpc,
      props.securityGroupProps
    );

    new Database(this, 'OrcaBusDatabaseConstruct', {
      vpc,
      allowedInboundSG: securityGroup.computeSecurityGroup,
      ...props.databaseProps,
    });

    new SchemaRegistryConstruct(this, 'SchemaRegistryConstruct', props.schemaRegistryProps);

    if (props.eventSourceProps) {
      new EventSource(this, 'EventSourceConstruct', props.eventSourceProps);
    }

    new IcaEventPipeStack(this, props.icaEventPipeProps.name, {
      env: {
        account: props.env?.account,
        region: 'ap-southeast-2',
      },
      ...props.icaEventPipeProps,
    });

    this.statefulStackArray.push(this.createTokenServiceStack(props));
  }

  private createTokenServiceStack(props: cdk.StackProps & OrcaBusStatefulConfig) {
    return new TokenServiceStack(this, 'TokenServiceStack', {
      // reduce the props to the stack needs
      env: props.env,
      ...props.tokenServiceProps,
    });
  }
}
