import path from 'path';
import * as cdk from 'aws-cdk-lib';
import { IBucket } from 'aws-cdk-lib/aws-s3';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { aws_lambda, Duration, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import { IEventBus, Rule } from 'aws-cdk-lib/aws-events';

export interface UniversalEventArchiverProps {
  securityGroups: ISecurityGroup[];
  vpc: IVpc;
  archiveBucket: IBucket;
  mainBus: IEventBus;
}

export class UniversalEventArchiverStack extends cdk.Stack {
  private readonly id: string;
  private readonly props: UniversalEventArchiverProps;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;

  constructor(scope: Construct, id: string, props: cdk.StackProps & UniversalEventArchiverProps) {
    super(scope, id, props);

    this.id = id;
    this.props = props;

    const eventBus = this.props.mainBus;
    const auditBucket = this.props.archiveBucket;

    const archiveEventFunction = new PythonFunction(this, 'UniversalEventArchiver', {
      entry: path.join(__dirname, '../function'),
      runtime: this.lambdaRuntimePythonVersion,
      environment: {
        BUCKET_NAME: auditBucket.bucketName,
      },
      securityGroups: this.props.securityGroups,
      vpc: this.props.vpc,
      vpcSubnets: { subnets: this.props.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
      timeout: Duration.minutes(5),
      index: 'archiver.py',
      handler: 'handler',
    });

    auditBucket.grantReadWrite(archiveEventFunction);

    const rule = new Rule(this, 'Rule', {
      eventBus,
      eventPattern: {
        //account: [cdk.Aws.ACCOUNT_ID],
        account: [Stack.of(this).account],
      },
    });

    rule.addTarget(
      new LambdaFunction(archiveEventFunction, {
        maxEventAge: Duration.minutes(10), // Maximum age for an event to be retried
        retryAttempts: 3, // Retry up to 3 times
      })
    );

    // Optional: If the Lambda function needs more permissions
    archiveEventFunction.addToRolePolicy(
      new PolicyStatement({
        actions: ['s3:PutObject'],
        resources: [auditBucket.bucketArn + '/*'],
      })
    );
  }
}
