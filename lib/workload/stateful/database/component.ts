import { Construct } from 'constructs';
import { aws_ec2, aws_rds, RemovalPolicy } from 'aws-cdk-lib';
import { AuroraPostgresEngineVersion, Credentials } from 'aws-cdk-lib/aws-rds';
import { IVpc } from 'aws-cdk-lib/aws-ec2';

export interface Props {
  vpc: IVpc;
}

export class DatabaseConstruct extends Construct {
  private cluster: aws_rds.ServerlessCluster;

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);

    const secret = new aws_rds.DatabaseSecret(this, 'AuroraSecret', {
      username: 'admin',
    });

    this.cluster = new aws_rds.ServerlessCluster(this, 'OrcaBus', {
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: aws_ec2.SubnetType.PRIVATE_ISOLATED,
      },
      engine: aws_rds.DatabaseClusterEngine.auroraPostgres({
        version: AuroraPostgresEngineVersion.VER_14_6,
      }),
      parameterGroup: aws_rds.ParameterGroup.fromParameterGroupName(
        this,
        'ParameterGroup',
        'default.aurora-postgresql14',
      ),
      removalPolicy: RemovalPolicy.DESTROY,
      scaling: {
        // autoPause: Duration.seconds(60),
        minCapacity: aws_rds.AuroraCapacityUnit.ACU_1,
        maxCapacity: aws_rds.AuroraCapacityUnit.ACU_2,
      },
      credentials: Credentials.fromSecret(secret),
      clusterIdentifier: 'orcabus-db',
      defaultDatabaseName: 'orcabus',
    });
  }
}
