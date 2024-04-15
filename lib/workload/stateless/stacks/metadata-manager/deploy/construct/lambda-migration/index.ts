import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { PythonFunction, PythonFunctionProps } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';

type LambdaProps = {
  /**
   * The basic common lambda properties that it should inherit from
   */
  basicLambdaConfig: PythonFunctionProps;
  /**
   * The secret for the db connection where the lambda will need access to
   */
  dbConnectionSecret: ISecret;
};

export class LambdaMigrationConstruct extends Construct {
  private readonly lambda: PythonFunction;

  constructor(scope: Construct, id: string, lambdaProps: LambdaProps) {
    super(scope, id);

    this.lambda = new PythonFunction(this, 'MigrationLambda', {
      ...lambdaProps.basicLambdaConfig,
      index: 'handler/migrate.py',
      handler: 'handler',
      timeout: Duration.minutes(2),
    });
    lambdaProps.dbConnectionSecret.grantRead(this.lambda);
  }
}
