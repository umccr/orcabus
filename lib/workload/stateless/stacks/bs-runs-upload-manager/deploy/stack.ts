import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { BsRunsUploadManagerConstruct } from './constructs/bs-runs-upload-manager';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../constructs/python-lambda-layer';

export interface BsRunsUploadManagerConfig {
  // Define construct properties here
  ica_token_secret_id: string; // IcaSecretsPortal
  portal_token_secret_id: string; // orcabus/token-service-jwt
  basespace_token_secret_id: string; // /manual/BaseSpaceAccessTokenSecret
  gds_system_files_path: string; // gds://development/primary_data/temp/bs_runs_upload_tes/
  eventbus_name: string; // /umccr/orcabus/stateful/eventbridge
}

export type BsRunsUploadManagerStackProps = BsRunsUploadManagerConfig & cdk.StackProps;

export class BsRunsUploadManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BsRunsUploadManagerStackProps) {
    super(scope, id, props);

    // Set lambda layer arn object
    const lambda_layer_obj = new PythonLambdaLayerConstruct(
      this,
      'bssh_tools_lambda_layer',
      {
        layer_name: "BSSHToolsLambdaLayer",
        layer_description: 'layer to enable the manager tools layer',
        layer_directory: path.join(__dirname, '../layers')
    });

    const ica_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'IcaSecretsPortalSecretObject',
      props.ica_token_secret_id
    );

    const portal_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'PortalSecret',
      props.portal_token_secret_id
    );

    const basespace_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this,
      'BaseSpaceAccessTokenSecret',
      props.basespace_token_secret_id
    );

    const event_bus_obj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventbus_name);

    new BsRunsUploadManagerConstruct(this, 'bs-runs-upload-manager', {
      /* Stack objects */
      lambda_layer_obj: lambda_layer_obj,
      ica_token_secret_obj: ica_access_token_secret_obj,
      portal_token_secret_obj: portal_secret_obj,
      basespace_secret_obj: basespace_secret_obj,
      event_bus_obj: event_bus_obj,
      /* Lambda paths */
      upload_v2_samplesheet_to_gds_bssh_lambda_path: path.join(
        __dirname,
        '../lambdas/upload_v2_samplesheet_to_gds_bssh'
      ),
      launch_bs_runs_upload_tes_lambda_path: path.join(
        __dirname,
        '../lambdas/launch_bs_runs_upload_tes'
      ),
      /* Step functions templates */
      workflow_definition_body_path: path.join(
        __dirname,
        '../step_functions_templates/bs_runs_upload_step_functions_template.json'
      ),
      /* Miscell */
      gds_system_files_path: props.gds_system_files_path,
    });
  }
}
