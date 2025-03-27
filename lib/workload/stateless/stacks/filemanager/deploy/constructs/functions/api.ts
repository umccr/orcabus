import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';
import { BucketProps } from './ingest';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';

/**
 * Props for the API function.
 */
export type ApiFunctionProps = fn.FunctionPropsConfigurable &
  DatabaseProps &
  BucketProps & {
    accessKeySecretArn: string;
  };

/**
 * A construct for the Lambda API function.
 */
export class ApiFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: ApiFunctionProps) {
    super(scope, id, {
      package: 'filemanager-api-lambda',
      environment: {
        // This ensures that the API Gateway stage is not included when processing a request.
        // See https://github.com/awslabs/aws-lambda-rust-runtime/tree/main/lambda-http#integration-with-api-gateway-stages
        // for more info.
        AWS_LAMBDA_HTTP_IGNORE_STAGE_IN_PATH: 'true',
        FILEMANAGER_ACCESS_KEY_SECRET_ID: props.accessKeySecretArn,
        ...props.environment,
      },
      ...props,
    });

    // Allow access to the access key secret.
    this.role.addToPolicy(
      new PolicyStatement({
        actions: ['secretsmanager:GetSecretValue'],
        resources: [`${props.accessKeySecretArn}-*`],
      })
    );
  }
}
