import { Construct } from 'constructs';
import { RustFunction } from 'rust.aws-cdk-lambda';
import { Duration } from 'aws-cdk-lib';
import { Settings as CargoSettings } from 'rust.aws-cdk-lambda/dist/settings';
import { IDatabase } from '../../../../../stateful/database/component';
import { IVpc, SecurityGroup, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { Architecture, IDestination, Version } from 'aws-cdk-lib/aws-lambda';
import { ManagedPolicy, PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';


/**
 * Settable values for a Rust function.
 */
export type FunctionSettings = {
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
 * Props for a Rust function without the package.
 */
export type FunctionPropsNoPackage = FunctionSettings & {
  /**
   * Vpc for the function.
   */
  readonly vpc: IVpc;
  /**
   * Database that the function uses.
   */
  readonly database: IDatabase;
  /**
   * The destination to post failed invocations to.
   */
  readonly onFailure?: IDestination;
  /**
   * Name of the Lambda function resource.
   */
  readonly functionName?: string;
};

/**
 * Props for the Rust function.
 */
export type FunctionProps = FunctionPropsNoPackage & {
  /**
   * The package to build for this function.
   */
  readonly package: string;
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
    this._role = new Role(this, 'Role', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + id,
    });
    // Lambda needs VPC access if it is created in a VPC.
    this.addManagedPolicy('service-role/AWSLambdaVPCAccessExecutionRole');

    // Lambda needs to be able to reach out to access S3, security manager (eventually), etc.
    // Could this use an endpoint instead?
    const securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: props.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows a filemanager Lambda function to egress out.',
    });

    CargoSettings.BUILD_INDIVIDUALLY = true;

    this._function = new RustFunction(this, 'RustFunction', {
      package: props.package,
      target: 'aarch64-unknown-linux-gnu',
      memorySize: 128,
      timeout: Duration.seconds(28),
      environment: {
        // Todo use security manager to get connection string rather than passing it in as an environment variable
        DATABASE_URL: props.database.unsafeConnection,
        RUST_LOG:
          props.rustLog ?? `info,${props.package.replace('-', '_')}=trace,filemanager=trace`,
      },
      buildEnvironment: props.buildEnvironment,
      extraBuildArgs: ['--manifest-path', `../${props.package}/Cargo.toml`],
      architecture: Architecture.ARM_64,
      role: this._role,
      onFailure: props.onFailure,
      vpc: props.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [
        securityGroup,
        // Allow access to database.
        props.database.securityGroup,
      ],
      functionName: props.functionName,
    });

    // Todo this should probably connect to an RDS proxy rather than directly to the database.
  }

  /**
   * Add a managed policy to the function's role.
   */
  addManagedPolicy(policyName: string) {
    this._role.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName(policyName));
  }

  /**
   * Add a policy statement to this function's role.
   */
  addToPolicy(policyStatement: PolicyStatement) {
    this._role.addToPolicy(policyStatement)
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
