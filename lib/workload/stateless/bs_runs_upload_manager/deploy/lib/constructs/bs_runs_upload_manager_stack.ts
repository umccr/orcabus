import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';
import { IRole } from 'aws-cdk-lib/aws-iam';

interface BsRunsUploadManagerConstructProps {
  lambdas_layer_path: string; // __dirname + '/../../../layers
  upload_v2_samplesheet_to_gds_bssh_lambda_path: string; // __dirname + '/../../../lambdas/upload_v2_samplesheet_to_gds_bssh'
  launch_bs_runs_upload_tes_lambda_path: string; // __dirname + '/../../../lambdas/launch_bs_runs_upload_tes'
  ica_token_secret_id: string; // IcaSecretsPortal
  gds_system_files_path: string; // gds://development/primary_data/temp/bs_runs_upload_tes/
  workflow_definition_body_path: string; // __dirname + '/../../../step_functions_templates/bs_runs_upload_step_functions_template.json'
}

export class BsRunsUploadManagerConstruct extends Construct {

  public readonly bs_runs_upload_event_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: BsRunsUploadManagerConstructProps) {
    super(scope, id);

    // Set lambda layer arn object
    const lambda_layer = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: props.lambdas_layer_path,
      });

    const ica_access_token_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this, 'IcaSecretsPortalSecretObject',
      props.ica_token_secret_id,
    );

    const portal_secret_obj = secretsManager.Secret.fromSecretNameV2(
      this, 'PortalSecret',
      'PortalSecret4BsshUploads',
    ); // FIXME: This is a temp hack and has to be updated every half-hour

    const basespace_secret_obj = new secretsManager.Secret(
      this, 'BaseSpaceAccessTokenSecret',
      {
        secretName: 'BaseSpaceAccessTokenSecret'
      }
    )

    // V2 Upload lambda
    const upload_v2_samplesheet_to_gds_bssh_lambda = new PythonFunction(this, 'upload_v2_samplesheet_to_gds_bssh_lambda', {
      entry: props.upload_v2_samplesheet_to_gds_bssh_lambda_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [lambda_layer.lambda_layer_version_obj],
      // @ts-ignore
      timeout: Duration.seconds(60),
      environment: {
        ICA_BASE_URL: "https://aps2.platform.illumina.com",
        ICA_ACCESS_TOKEN_SECRET_ID: ica_access_token_secret_obj.secretName,
        PORTAL_TOKEN_SECRET_ID: portal_secret_obj.secretName,
      }
    });

    // Launch BS Runs Upload TES lambda
    const launch_bs_runs_upload_tes_lambda = new PythonFunction(this, 'launch_bs_runs_upload_tes_lambda',
      {
        entry: props.launch_bs_runs_upload_tes_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [lambda_layer.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
        environment: {
          BASESPACE_API_SERVER: "https://api.aps2.sh.basespace.illumina.com",
          BASESPACE_ACCESS_TOKEN_SECRET_ID: basespace_secret_obj.secretName,
          ICA_BASE_URL: "https://aps2.platform.illumina.com",
          ICA_ACCESS_TOKEN_SECRET_ID: ica_access_token_secret_obj.secretName,
          GDS_SYSTEM_FILES_PATH: props.gds_system_files_path,
        }
      }

    )

    // Give the lambda permission to read the ICA ACCESS TOKEN secret
    ica_access_token_secret_obj.grantRead(
      // @ts-ignore
      <IRole>launch_bs_runs_upload_tes_lambda.role
    );
    ica_access_token_secret_obj.grantRead(
      // @ts-ignore
      <IRole>upload_v2_samplesheet_to_gds_bssh_lambda.role
    );

    // Give the lambda permission to read the PORTAL TOKEN secret
    // FIXME - remove once we have a better way of collecting the portal token
    portal_secret_obj.grantRead(
      // @ts-ignore
      <IRole>upload_v2_samplesheet_to_gds_bssh_lambda.role
    );

    // Give basespace upload lambda permission to read the basespace access token secret
    basespace_secret_obj.grantRead(
      // @ts-ignore
      <IRole>launch_bs_runs_upload_tes_lambda.role
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'bs_runs_upload_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflow_definition_body_path),
      // definitionSubstitutions
      definitionSubstitutions: {
        '__upload_v2_samplesheet_to_gds_bssh_function_arn__': upload_v2_samplesheet_to_gds_bssh_lambda.functionArn,
        '__launch_bs_runs_upload_tes_function_arn__': launch_bs_runs_upload_tes_lambda.functionArn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            upload_v2_samplesheet_to_gds_bssh_lambda.functionArn,
            launch_bs_runs_upload_tes_lambda.functionArn,
          ],
          actions: [
            'lambda:InvokeFunction',
          ],
        },
      ),
    );
    
    // Set outputs
    this.bs_runs_upload_event_state_machine_arn = stateMachine.stateMachineArn;
  }

}
