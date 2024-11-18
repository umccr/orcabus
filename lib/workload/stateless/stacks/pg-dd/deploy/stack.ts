import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import {
  ISecurityGroup,
  IVpc,
  SecurityGroup,
  SubnetType,
  Vpc,
  VpcLookupOptions,
} from 'aws-cdk-lib/aws-ec2';
import { NamedLambdaRole } from '../../../../components/named-lambda-role';
import { ManagedPolicy, PolicyStatement, Role } from 'aws-cdk-lib/aws-iam';
import { readFileSync } from 'fs';

/**
 * Props for the PgDD stack.
 */
export type PgDDStackProps = {
  /**
   * The bucket to dump data to.
   */
  bucket: string;
  /**
   * Secret to connect to database with.
   */
  secretArn: string;
  /**
   * The key prefix when writing data.
   */
  prefix?: string;
  /**
   * Props to lookup the VPC with.
   */
  vpcProps: VpcLookupOptions;
  /**
   * Existing security group name to be attached on lambda.
   */
  lambdaSecurityGroupName: string;
};

/**
 * Deploy the PgDD stack.
 */
export class PgDDStack extends Stack {
  private readonly vpc: IVpc;
  private readonly securityGroup: ISecurityGroup;
  private readonly role: Role;

  constructor(scope: Construct, id: string, props: StackProps & PgDDStackProps) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.securityGroup = SecurityGroup.fromLookupByName(
      this,
      'OrcaBusLambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      this.vpc
    );

    this.role = new NamedLambdaRole(this, 'Role');
    this.role.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole')
    );
    this.role.addToPolicy(
      new PolicyStatement({
        actions: ['s3:PutObject'],
        resources: [`arn:aws:s3:::${props.bucket}`, `arn:aws:s3:::${props.bucket}/*`],
      })
    );
    this.role.addToPolicy(
      new PolicyStatement({
        actions: ['secretsmanager:GetSecretValue'],
        resources: [`${props.secretArn}-*`],
      })
    );

    const securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: this.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows the PgDD Lambda function to egress out.',
    });

    const entry = path.join(__dirname, '..');
    new PythonFunction(this, 'function', {
      entry,
      functionName: 'orcabus-pg-dd',
      index: 'pg_dd/handler.py',
      runtime: Runtime.PYTHON_3_12,
      architecture: Architecture.ARM_64,
      timeout: Duration.minutes(15),
      memorySize: 1024,
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      },
      bundling: {
        assetExcludes: [...readFileSync(path.join(entry, '.dockerignore'), 'utf-8').split('\n')],
      },
      role: this.role,
      securityGroups: [securityGroup, this.securityGroup],
      environment: {
        PG_DD_SECRET: props.secretArn,
        PG_DD_BUCKET: props.bucket,
        PG_DD_DATABASE_METADATA_MANAGER: 'metadata_manager',
        PG_DD_DATABASE_SEQUENCE_RUN_MANAGER: 'sequence_run_manager',
        PG_DD_DATABASE_WORKFLOW_MANAGER: 'workflow_manager',
        PG_DD_DATABASE_FILEMANAGER: 'filemanager',
        ...(props.prefix && { PG_DD_PREFIX: props.prefix }),
      },
    });
  }
}
