import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { EventBusConstruct } from './stateful/eventbridge/component';
import { DatabaseConstruct } from './stateful/database/component';
import { SecurityGroupConstruct } from './stateful/securitygroup/component';

export class OrcaBusStatefulStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // --- Constructs pre-existing resources

    const vpc = getVpc(this);

    // --- Create Stateful resources

    new EventBusConstruct(this, 'OrcaBusEventBusConstruct');
    new DatabaseConstruct(this, 'OrcaBusDatabaseConstruct', { vpc: vpc });
    new SecurityGroupConstruct(this, 'OrcaBusSecurityGroupConstruct', { vpc: vpc });
  }
}
