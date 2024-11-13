import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';
import { BucketProps } from './ingest';

/**
 * Props for the API function.
 */
export type ApiFunctionProps = fn.FunctionPropsConfigurable & DatabaseProps & BucketProps;

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
        FILEMANAGER_API_PRESIGN_EXPIRY: '12 hours',
        ...props.environment,
      },
      ...props,
    });

    this.addPoliciesForBuckets(props.buckets, fn.Function.getObjectActions());
  }
}
