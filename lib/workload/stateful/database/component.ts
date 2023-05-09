import { Construct } from 'constructs';
import { aws_ec2, aws_rds, RemovalPolicy } from 'aws-cdk-lib';
import { AuroraPostgresEngineVersion, Credentials } from 'aws-cdk-lib/aws-rds';
import { IVpc } from 'aws-cdk-lib/aws-ec2';

export interface DatabaseProps {
  clusterIdentifier: string;
  defaultDatabaseName: string;
  version: AuroraPostgresEngineVersion;
  parameterGroupName: string;
  username: string;
}

export class DatabaseConstruct extends Construct {
  constructor(scope: Construct, id: string, vpc: IVpc, props: DatabaseProps) {
    super(scope, id);

    const secret = new aws_rds.DatabaseSecret(this, id + 'Secret', {
      // username: 'admin',
      username: props.username,
    });

    new aws_rds.ServerlessCluster(this, id + 'Cluster', {
      vpc: vpc,
      vpcSubnets: {
        subnetType: aws_ec2.SubnetType.PRIVATE_ISOLATED,
      },
      engine: aws_rds.DatabaseClusterEngine.auroraPostgres({
        version: props.version,
      }),
      parameterGroup: aws_rds.ParameterGroup.fromParameterGroupName(
        this,
        id + 'ParameterGroup',
        props.parameterGroupName
      ),
      removalPolicy: RemovalPolicy.DESTROY,
      scaling: {
        // autoPause: Duration.seconds(60),
        minCapacity: aws_rds.AuroraCapacityUnit.ACU_1,
        maxCapacity: aws_rds.AuroraCapacityUnit.ACU_2,
      },
      credentials: Credentials.fromSecret(secret),
      clusterIdentifier: props.clusterIdentifier,
      defaultDatabaseName: props.defaultDatabaseName,
    });
  }
}
