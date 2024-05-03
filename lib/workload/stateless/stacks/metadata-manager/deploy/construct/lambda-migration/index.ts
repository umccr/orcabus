import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { PythonFunction, PythonFunctionProps } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { ProviderFunction } from '../../../../../../components/provider-function';
import { IVpc } from 'aws-cdk-lib/aws-ec2';

type LambdaProps = {
  /**
   * The basic common lambda properties that it should inherit from
   */
  basicLambdaConfig: PythonFunctionProps;
  /**
   * The secret for the db connection where the lambda will need access to
   */
  dbConnectionSecret: ISecret;
  /**
   * VPC used for Custom Provider Function
   */
  vpc: IVpc;
};

export class LambdaMigrationConstruct extends Construct {
  private readonly lambda: PythonFunction;

  constructor(scope: Construct, id: string, props: LambdaProps) {
    super(scope, id);

    this.lambda = new PythonFunction(this, 'MigrationLambda', {
      ...props.basicLambdaConfig,
      index: 'handler/migrate.py',
      handler: 'handler',
      timeout: Duration.minutes(2),
    });
    props.dbConnectionSecret.grantRead(this.lambda);

    new ProviderFunction(this, 'AutoMigrateLambdaFunction', {
      vpc: props.vpc,
      function: this.lambda,
    });
  }
}
