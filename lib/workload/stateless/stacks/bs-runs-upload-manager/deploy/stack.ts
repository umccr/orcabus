import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { BsRunsUploadManagerConstruct } from './constructs/bs-runs-upload-manager';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';

export interface BsRunsUploadManagerConfig {
  // Define construct properties here
  icaTokenSecretId: string; // IcaSecretsPortal
  portalTokenSecretId: string; // orcabus/token-service-jwt
  basespaceTokenSecretId: string; // /manual/BaseSpaceAccessTokenSecret
  ssCheckApiUrlSsmParameterName: string; // /data_portal/backend/api_domain_name
  gdsSystemFilesPath: string; // gds://development/primary_data/temp/bs_runs_upload_tes/
  eventbusName: string; // /umccr/orcabus/stateful/eventbridge
}

export type BsRunsUploadManagerStackProps = BsRunsUploadManagerConfig & cdk.StackProps;

export class BsRunsUploadManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BsRunsUploadManagerStackProps) {
    super(scope, id, props);

    // Set lambda layer arn object
    const lambda_layer_obj = new PythonLambdaLayerConstruct(this, 'bssh_tools_lambda_layer', {
      layerName: 'BSSHToolsLambdaLayer',
      layerDescription: 'layer to enable the manager tools layer',
      layerDirectory: path.join(__dirname, '../layers'),
    });

    const ica_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'IcaSecretsPortalSecretObject',
      props.icaTokenSecretId
    );

    const portal_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'PortalSecret',
      props.portalTokenSecretId
    );

    const basespace_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'BaseSpaceAccessTokenSecret',
      props.basespaceTokenSecretId
    );

    const ss_check_api_ssm_parameter_obj = ssm.StringParameter.fromStringParameterName(
      this,
      'DataPortalApiUrlSsmParameter',
      props.ssCheckApiUrlSsmParameterName
    );

    const event_bus_obj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventbusName);

    new BsRunsUploadManagerConstruct(this, 'bs-runs-upload-manager', {
      /* Stack objects */
      lambdaLayerObj: lambda_layer_obj,
      icaTokenSecretObj: ica_access_token_secret_obj,
      portalTokenSecretObj: portal_secret_obj,
      basespaceSecretObj: basespace_secret_obj,
      ssCheckApiUrlSsmParameterObj: ss_check_api_ssm_parameter_obj,
      eventBusObj: event_bus_obj,
      /* Lambda paths */
      uploadV2SamplesheetToGdsBsshLambdaPath: path.join(
        __dirname,
        '../lambdas/upload_v2_samplesheet_to_gds_bssh'
      ),
      launchBsRunsUploadTesLambdaPath: path.join(__dirname, '../lambdas/launch_bs_runs_upload_tes'),
      /* Step functions templates */
      workflowDefinitionBodyPath: path.join(
        __dirname,
        '../step_functions_templates/bs_runs_upload_step_functions_template.json'
      ),
      /* Miscell */
      gdsSystemFilesPath: props.gdsSystemFilesPath,
    });
  }
}
