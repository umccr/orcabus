import path from 'path';
import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { PythonFunction, PythonFunctionProps } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import {
  DockerImageFunction,
  DockerImageFunctionProps,
  DockerImageCode,
} from 'aws-cdk-lib/aws-lambda';

type LambdaProps = {
  /**
   * The basic common lambda properties that it should inherit from
   */
  basicLambdaConfig: Partial<DockerImageFunctionProps>;
  /**
   * The secret for the db connection where the lambda will need access to
   */
  dbConnectionSecret: ISecret;
};

export class LambdaSyncGsheetConstruct extends Construct {
  private readonly GDRIVE_CRED_PARAM_NAME = '/umccr/google/drive/lims_service_account_json';
  private readonly GDRIVE_SHEET_ID_PARAM_NAME = '/umccr/google/drive/tracking_sheet_id';

  private readonly lambda: PythonFunction;

  constructor(scope: Construct, id: string, lambdaProps: LambdaProps) {
    super(scope, id);

    this.lambda = new DockerImageFunction(this, 'SyncGSheetLambda', {
      environment: {
        ...lambdaProps.basicLambdaConfig.environment,
        SSM_NAME_GDRIVE_ACCOUNT: this.GDRIVE_CRED_PARAM_NAME,
        SSM_NAME_TRACKING_SHEET_ID: this.GDRIVE_SHEET_ID_PARAM_NAME,
      },
      securityGroups: lambdaProps.basicLambdaConfig.securityGroups,
      vpc: lambdaProps.basicLambdaConfig.vpc,
      vpcSubnets: lambdaProps.basicLambdaConfig.vpcSubnets,
      architecture: lambdaProps.basicLambdaConfig.architecture,
      code: DockerImageCode.fromImageAsset(path.join(__dirname, '../../../'), {
        file: 'deploy/construct/lambda-sync-gsheet/lambda.Dockerfile',
      }),
      timeout: Duration.minutes(15),
    });

    lambdaProps.dbConnectionSecret.grantRead(this.lambda);

    // the sync-db lambda would need some cred to access GDrive and these are stored in SSM
    const trackingSheetCredSSM = StringParameter.fromSecureStringParameterAttributes(
      this,
      'GSheetCredSSM',
      { parameterName: this.GDRIVE_CRED_PARAM_NAME }
    );
    const trackingSheetIdSSM = StringParameter.fromSecureStringParameterAttributes(
      this,
      'TrackingSheetIdSSM',
      { parameterName: this.GDRIVE_SHEET_ID_PARAM_NAME }
    );
    trackingSheetCredSSM.grantRead(this.lambda);
    trackingSheetIdSSM.grantRead(this.lambda);
  }
}
