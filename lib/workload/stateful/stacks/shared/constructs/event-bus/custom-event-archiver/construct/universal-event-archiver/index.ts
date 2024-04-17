import path from 'path';
import { IBucket } from 'aws-cdk-lib/aws-s3';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { aws_lambda, Duration, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import { IVpc } from 'aws-cdk-lib/aws-ec2';

export interface UniversalEventArchiverConstructProps {
  vpc: IVpc;
  archiveBucket: IBucket;
  eventBus: IEventBus;
}

export class UniversalEventArchiverConstruct extends Construct {
  private readonly id: string;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;

  constructor(scope: Construct, id: string, props: UniversalEventArchiverConstructProps) {
    super(scope, id);

    this.id = id;

    const eventBus = props.eventBus;
    const archiveBucket = props.archiveBucket;

    const archiveEventFunction = new PythonFunction(this, 'UniversalEventArchiver', {
      entry: path.join(__dirname, '../../archiver-service'),
      runtime: this.lambdaRuntimePythonVersion,
      environment: {
        BUCKET_NAME: archiveBucket.bucketName,
      },
      vpc: props.vpc,
      vpcSubnets: { subnets: props.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      index: 'universal_event_achiver.py',
      handler: 'handler',
    });

    archiveBucket.grantReadWrite(archiveEventFunction);

    const rule = new Rule(this, 'Rule', {
      eventBus,
      eventPattern: {
        //account: [cdk.Aws.ACCOUNT_ID],
        account: [Stack.of(this).account],
      },
    });

    rule.addTarget(
      new LambdaFunction(archiveEventFunction, {
        maxEventAge: Duration.seconds(28), // Maximum age for an event to be retried
        retryAttempts: 3, // Retry up to 3 times
      })
    );

    // Optional: If the Lambda function needs more permissions
    archiveEventFunction.addToRolePolicy(
      new PolicyStatement({
        actions: ['s3:PutObject'],
        resources: [archiveBucket.bucketArn + '/*'],
      })
    );
  }
}
