import { Construct } from 'constructs';
import { IVpc, SecurityGroup, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { RustFunction } from 'rust.aws-cdk-lambda';
import { Duration } from 'aws-cdk-lib';
import { Architecture, Function, IDestination } from 'aws-cdk-lib/aws-lambda';
import { Database } from '../database';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Settings as CargoSettings } from 'rust.aws-cdk-lambda/dist/settings';
import { IPolicy, PolicyStatement } from 'aws-cdk-lib/aws-iam';

/**
 * Settable values for the ingest function.
 */
export type IngestFunctionSettings = {
  /**
   * Additional build environment variables when building the Lambda function.
   */
  readonly buildEnvironment?: { [key: string]: string | undefined };
  /**
   * RUST_LOG string, defaults to trace on local crates and info everywhere else.
   */
  readonly rustLog?: string;
};

/**
 * Props for the database
 */
export type IngestFunctionProps = IngestFunctionSettings & {
  /**
   * Vpc for the function.
   */
  readonly vpc: IVpc;
  /**
   * Database that the function uses.
   */
  readonly database: Database;
  /**
   * The SQS queue URL to receive events from.
   */
  readonly queue: IQueue;
  /**
   * The destination to post failed invocations to.
   */
  readonly onFailure?: IDestination;
  /**
   * Additional policies to add to the Lambda role.
   */
  readonly policies?: PolicyStatement[];
};

/**
 * A construct for the Lambda ingest function.
 */
export class IngestFunction extends Construct {
  private readonly _function: RustFunction;

  constructor(scope: Construct, id: string, props: IngestFunctionProps) {
    super(scope, id);

    // Lambda role needs SQS execution role.
    const lambdaRole = new iam.Role(this, id + 'Role', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + id,
    });
    lambdaRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaSQSQueueExecutionRole')
    );
    props.policies?.forEach((policy) => {
      lambdaRole.addToPolicy(policy);
    });

    // Lambda needs to be able to reach out to access S3, security manager (eventually), etc.
    // Could this use an endpoint instead?
    const securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: props.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows the ingest Lambda function to egress out.',
    });

    CargoSettings.WORKSPACE_DIR = '../';
    CargoSettings.BUILD_INDIVIDUALLY = true;

    const filemanagerLambda = new RustFunction(this, 'IngestLambdaFunction', {
      package: 'filemanager-ingest-lambda',
      target: 'aarch64-unknown-linux-gnu',
      memorySize: 128,
      timeout: Duration.seconds(28),
      environment: {
        // Todo use security manager to get connection string rather than passing it in as an environment variable
        DATABASE_URL: props.database.unsafeConnection,
        RUST_LOG: props.rustLog ?? 'info,filemanager_ingest_lambda=trace,filemanager=trace',
      },
      buildEnvironment: props.buildEnvironment,
      architecture: Architecture.ARM_64,
      role: lambdaRole,
      onFailure: props.onFailure,
      vpc: props.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [
        securityGroup,
        // Allow access to database.
        props.database.securityGroup,
      ],
    });

    const eventSource = new lambdaEventSources.SqsEventSource(props.queue);
    filemanagerLambda.addEventSource(eventSource);

    // Todo this should probably connect to an RDS proxy rather than directly to the database.
  }

  /**
   * Get the Lambda function.
   */
  get function(): RustFunction {
    return this._function;
  }
}
