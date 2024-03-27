import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { BsRunsUploadManagerConstruct } from '../constructs/bs_runs_upload_manager_stack';
// import * as sqs from 'aws-cdk-lib/aws-sqs';

export interface BsRunsUploadManagerStackProps extends cdk.StackProps {
  // Define construct properties here
  ica_token_secret_id: string; // IcaSecretsPortal
  gds_system_files_path: string; // gds://development/primary_data/temp/bs_runs_upload_tes/
}

export class BsRunsUploadManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BsRunsUploadManagerStackProps) {
    super(scope, id, props);

    new BsRunsUploadManagerConstruct(
      this,
      'bs-runs-upload-manager',
      {
        lambdas_layer_path: __dirname + '/../../../layers',
        upload_v2_samplesheet_to_gds_bssh_lambda_path: __dirname + '/../../../lambdas/upload_v2_samplesheet_to_gds_bssh',
        launch_bs_runs_upload_tes_lambda_path: __dirname + '/../../../lambdas/launch_bs_runs_upload_tes',
        ica_token_secret_id: props.ica_token_secret_id,
        gds_system_files_path: props.gds_system_files_path,
        workflow_definition_body_path: __dirname + '/../../../step_functions_templates/bs_runs_upload_step_functions_template.json'
      }
    )
  }
}
