import path from 'path';
import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import {
  DockerImageFunction,
  DockerImageFunctionProps,
  DockerImageCode,
} from 'aws-cdk-lib/aws-lambda';
import { EventBus } from 'aws-cdk-lib/aws-events';

type LambdaProps = {
  /**
   * The basic common lambda properties that it should inherit from
   */
  basicLambdaConfig: Partial<DockerImageFunctionProps>;
  /**
   * The secret for the db connection where the lambda will need access to
   */
  dbConnectionSecret: ISecret;
  /**
   * The eventBusName to notify metadata state change
   */
  eventBusName: string;
};

export class LambdaLoadCustomCSVConstruct extends Construct {
  private readonly lambda: PythonFunction;

  constructor(scope: Construct, id: string, lambdaProps: LambdaProps) {
    super(scope, id);

    this.lambda = new DockerImageFunction(this, 'LoadCustomCSVLambda', {
      environment: {
        ...lambdaProps.basicLambdaConfig.environment,

        EVENT_BUS_NAME: lambdaProps.eventBusName,
      },
      securityGroups: lambdaProps.basicLambdaConfig.securityGroups,
      vpc: lambdaProps.basicLambdaConfig.vpc,
      vpcSubnets: lambdaProps.basicLambdaConfig.vpcSubnets,
      architecture: lambdaProps.basicLambdaConfig.architecture,
      code: DockerImageCode.fromImageAsset(path.join(__dirname, '../../../'), {
        file: 'deploy/construct/lambda-load-custom-csv/lambda.Dockerfile',
      }),
      timeout: Duration.minutes(15),
      memorySize: 4096,
    });

    lambdaProps.dbConnectionSecret.grantRead(this.lambda);

    // We need to store this lambda ARN somewhere so that we could refer when need to load this manually
    new StringParameter(this, 'LoadCustomCSVLambdaArnParameterStore', {
      parameterName: '/orcabus/metadata-manager/load-custom-csv-lambda-arn',
      description: 'The ARN of the lambda that load metadata from a presigned URL CSV file',
      stringValue: this.lambda.functionArn,
    });

    // The lambda will need permission to put events to the event bus when metadata state change
    const orcabusEventBus = EventBus.fromEventBusName(this, 'EventBus', lambdaProps.eventBusName);
    orcabusEventBus.grantPutEventsTo(this.lambda);
  }
}
