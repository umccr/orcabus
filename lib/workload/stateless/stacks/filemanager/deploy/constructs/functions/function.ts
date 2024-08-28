import { Construct } from 'constructs';
import { Duration, Stack } from 'aws-cdk-lib';
import { ISecurityGroup, IVpc, SecurityGroup, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { Architecture, Version } from 'aws-cdk-lib/aws-lambda';
import { ManagedPolicy, PolicyStatement, Role } from 'aws-cdk-lib/aws-iam';
import { RustFunction } from 'cargo-lambda-cdk';
import path from 'path';
import { exec } from 'cargo-lambda-cdk/lib/util';
import { randomUUID } from 'node:crypto';
import { print } from 'aws-cdk/lib/logging';
import { PostgresManagerStack } from '../../../../../../stateful/stacks/postgres-manager/deploy/stack';
import { FILEMANAGER_SERVICE_NAME } from '../../stack';
import { NamedLambdaRole } from '../../../../../../components/named-lambda-role';

/**
 * Properties for the database.
 */
export type DatabaseProps = {
  /**
   * The host of the database.
   */
  readonly host: string;
  /**
   * The port to connect with.
   */
  readonly port: number;
  /**
   * The database security group.
   */
  readonly securityGroup: ISecurityGroup;
};

/**
 * Props for a Rust function which can be configured from the top-level orcabus context.
 */
export type FunctionPropsConfigurable = {
  /**
   * Additional build environment variables when building the Lambda function.
   */
  readonly buildEnvironment?: { [key: string]: string };
  /**
   * Additional environment variables to set inside the Lambda function
   */
  readonly environment?: { [key: string]: string };
  /**
   * RUST_LOG string, defaults to trace on local crates and info everywhere else.
   */
  readonly rustLog?: string;
  /**
   * The role which the Function assumes.
   */
  readonly role?: Role;
  /**
   * Vpc for the function.
   */
  readonly vpc: IVpc;
};

/**
 * Props for the Rust function which can be configured from the top-level orcabus context.
 */
export type FunctionProps = FunctionPropsConfigurable &
  DatabaseProps & {
    /**
     * The package to build for this function.
     */
    readonly package: string;
    /**
     * Name of the Lambda function resource.
     */
    readonly functionName?: string;
    /**
     * The timeout for the Lambda function, defaults to 28 seconds.
     */
    readonly timeout?: Duration;
  };

/**
 * A construct for a Rust Lambda function.
 */
export class Function extends Construct {
  private readonly _function: RustFunction;
  private readonly _role: Role;

  constructor(scope: Construct, id: string, props: FunctionProps) {
    super(scope, id);

    // Lambda role needs SQS execution role.
    this._role = props.role ?? new NamedLambdaRole(this, 'Role');
    // Lambda needs VPC access if it is created in a VPC.
    this.addAwsManagedPolicy('service-role/AWSLambdaVPCAccessExecutionRole');
    // Using RDS IAM credentials, so we add the managed policy created by the postgres manager.
    this.addCustomerManagedPolicy(
      PostgresManagerStack.formatRdsPolicyName(FILEMANAGER_SERVICE_NAME)
    );

    // Lambda needs to be able to reach out to access S3, security manager, etc.
    // Could this use an endpoint instead?
    const securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: props.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows a filemanager Lambda function to egress out.',
    });

    const manifestPath = path.join(__dirname, '..', '..', '..');
    const uuid = randomUUID();

    // Don't bother creating a database if there is no bundling required.
    let localDatabaseUrl = undefined;
    if (Stack.of(this).bundlingRequired) {
      localDatabaseUrl = this.resolveLocalDatabaseUrl(uuid, manifestPath);
    }

    this._function = new RustFunction(this, 'RustFunction', {
      manifestPath: manifestPath,
      binaryName: props.package,
      bundling: {
        environment: {
          ...props.buildEnvironment,
          // The bundling process needs to be able to connect to the container running postgres.
          ...(localDatabaseUrl && { DATABASE_URL: localDatabaseUrl }),
        },
        dockerOptions: {
          network: 'host',
        },
      },
      memorySize: 128,
      timeout: props.timeout ?? Duration.seconds(28),
      environment: {
        // No password here, using RDS IAM to generate credentials.
        PGHOST: props.host,
        PGPORT: props.port.toString(),
        PGDATABASE: FILEMANAGER_SERVICE_NAME,
        PGUSER: FILEMANAGER_SERVICE_NAME,
        RUST_LOG:
          props.rustLog ?? `info,${props.package.replace('-', '_')}=trace,filemanager=trace`,
        ...props.environment,
      },
      architecture: Architecture.ARM_64,
      role: this._role,
      vpc: props.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [
        securityGroup,
        // Allow access to database.
        props.securityGroup,
      ],
      functionName: props.functionName,
    });

    // TODO: this should probably connect to an RDS proxy rather than directly to the database.
  }

  /**
   * Resolve the local database url for checking compiled queries.
   */
  private resolveLocalDatabaseUrl(uuid: string, manifestPath: string) {
    const execMake = (commandArgs: string) => {
      print(`running \`make ${commandArgs}\``);
      return exec('make', [commandArgs], { cwd: manifestPath, shell: true });
    };

    print('trying to find running filemanager container');

    // Check to see if there is a running database, no need to create these unnecessarily.
    let commandArgs = `-s docker-find DOCKER_PROJECT_NAME=${FILEMANAGER_SERVICE_NAME}`;
    let output = execMake(commandArgs);

    if (!output.stdout.toString()) {
      print('could not find a running filemanager container, starting a new one');

      // This starts the container running postgres in order to compile queries using sqlx.
      // It needs to be executed outside `beforeBundling`, because `beforeBundling` can run inside
      // the container context, and docker compose needs to run outside of this context.
      commandArgs = `-s docker-run DOCKER_PROJECT_NAME=${FILEMANAGER_SERVICE_NAME}-${uuid}`;
      output = execMake(commandArgs);
    }

    // Grab the last line only in case there are other outputs.
    const address = output.stdout.toString().trim().match('.*$')?.pop();
    const localDatabaseUrl = `postgresql://${FILEMANAGER_SERVICE_NAME}:${FILEMANAGER_SERVICE_NAME}@${address}/${FILEMANAGER_SERVICE_NAME}`; // pragma: allowlist secret
    print(`the local filemanager database url is: ${localDatabaseUrl}`);

    return localDatabaseUrl;
  }

  /**
   * Add an AWS managed policy to the function's role.
   */
  addAwsManagedPolicy(policyName: string) {
    this._role.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName(policyName));
  }

  /**
   * Add a customer managed policy to the function's role.
   */
  addCustomerManagedPolicy(policyName: string) {
    this._role.addManagedPolicy(ManagedPolicy.fromManagedPolicyName(this, 'Policy', policyName));
  }

  /**
   * Add a policy statement to this function's role.
   */
  addToPolicy(policyStatement: PolicyStatement) {
    this._role.addToPolicy(policyStatement);
  }

  /**
   * Add policies for 's3:List*' and 's3:Get*' on the buckets to this function's role.
   */
  addPoliciesForBuckets(buckets: string[]) {
    buckets.map((bucket) => {
      this.addToPolicy(
        new PolicyStatement({
          actions: ['s3:ListBucket', 's3:GetObject'],
          resources: [`arn:aws:s3:::${bucket}`, `arn:aws:s3:::${bucket}/*`],
        })
      );
    });
  }

  /**
   * Get the function name.
   */
  get functionName(): string {
    return this.function.functionName;
  }

  /**
   * Get the function version.
   */
  get currentVersion(): Version {
    return this.function.currentVersion;
  }

  /**
   * Get the function IAM role.
   */
  get role(): Role {
    return this._role;
  }

  /**
   * Get the Lambda function.
   */
  get function(): RustFunction {
    return this._function;
  }
}
