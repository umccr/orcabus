import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { IRole } from 'aws-cdk-lib/aws-iam';
import { PythonLambdaLayerConstruct } from '../../../../../../components/python-lambda-layer';

interface BsRunsUploadManagerConstructProps {
  /* Stack objects */
  lambda_layer_obj: PythonLambdaLayerConstruct;
  ica_token_secret_obj: secretsManager.ISecret;
  portal_token_secret_obj: secretsManager.ISecret;
  basespace_secret_obj: secretsManager.ISecret;
  event_bus_obj: events.IEventBus;
  /* Lambda layer paths */
  upload_v2_samplesheet_to_gds_bssh_lambda_path: string; //
  // __dirname + '/../../../lambdas/upload_v2_samplesheet_to_gds_bssh'
  launch_bs_runs_upload_tes_lambda_path: string; // __dirname + '/../../../lambdas/launch_bs_runs_upload_tes'
  /* Step function templates */
  gds_system_files_path: string; // gds://development/primary_data/temp/bs_runs_upload_tes/
  /* Miscell */
  workflow_definition_body_path: string; // __dirname + '/../../../step_functions_templates/bs_runs_upload_step_functions_template.json'
}

export class BsRunsUploadManagerConstruct extends Construct {
  public readonly bs_runs_upload_event_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: BsRunsUploadManagerConstructProps) {
    super(scope, id);

    // V2 Upload lambda
    const upload_v2_samplesheet_to_gds_bssh_lambda = new PythonFunction(
      this,
      'upload_v2_samplesheet_to_gds_bssh_lambda',
      {
        entry: props.upload_v2_samplesheet_to_gds_bssh_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        timeout: Duration.seconds(60),
        environment: {
          ICA_BASE_URL: 'https://aps2.platform.illumina.com',
          ICA_ACCESS_TOKEN_SECRET_ID: props.ica_token_secret_obj.secretName,
          PORTAL_TOKEN_SECRET_ID: props.portal_token_secret_obj.secretName,
        },
      }
    );

    // Launch BS Runs Upload TES lambda
    const launch_bs_runs_upload_tes_lambda = new PythonFunction(
      this,
      'launch_bs_runs_upload_tes_lambda',
      {
        entry: props.launch_bs_runs_upload_tes_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        timeout: Duration.seconds(60),
        environment: {
          BASESPACE_API_SERVER: 'https://api.aps2.sh.basespace.illumina.com',
          BASESPACE_ACCESS_TOKEN_SECRET_ID: props.basespace_secret_obj.secretName,
          ICA_BASE_URL: 'https://aps2.platform.illumina.com',
          ICA_ACCESS_TOKEN_SECRET_ID: props.ica_token_secret_obj.secretName,
          GDS_SYSTEM_FILES_PATH: props.gds_system_files_path,
        },
      }
    );

    // Give the lambda permission to read the ICA ACCESS TOKEN secret
    [launch_bs_runs_upload_tes_lambda, upload_v2_samplesheet_to_gds_bssh_lambda].forEach(
      (lambda_obj) => {
        props.ica_token_secret_obj.grantRead(<IRole>lambda_obj.role);
        props.portal_token_secret_obj.grantRead(<IRole>lambda_obj.role);
      }
    );

    // Give the lambda permission to read the PORTAL TOKEN secret
    props.portal_token_secret_obj.grantRead(
      // @ts-ignore
      <IRole>upload_v2_samplesheet_to_gds_bssh_lambda.role
    );

    // Give basespace upload lambda permission to read the basespace access token secret
    props.basespace_secret_obj.grantRead(
      // @ts-ignore
      <IRole>launch_bs_runs_upload_tes_lambda.role
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'bs_runs_upload_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflow_definition_body_path),
      // definitionSubstitutions
      definitionSubstitutions: {
        __upload_v2_samplesheet_to_gds_bssh_function_arn__:
          upload_v2_samplesheet_to_gds_bssh_lambda.functionArn,
        __launch_bs_runs_upload_tes_function_arn__: launch_bs_runs_upload_tes_lambda.functionArn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          upload_v2_samplesheet_to_gds_bssh_lambda.functionArn,
          launch_bs_runs_upload_tes_lambda.functionArn,
        ],
        actions: ['lambda:InvokeFunction'],
      })
    );

    // Trigger state machine on event
    const rule = new events.Rule(this, 'bs_runs_upload_event_rule', {
      eventBus: props.event_bus_obj,
      eventPattern: {
        source: ['orcabus.srm'],
        detailType: ['SequenceRunStateChange'],
        detail: {
          status: ['succeeded'],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new events_targets.SfnStateMachine(stateMachine, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    // Set outputs
    this.bs_runs_upload_event_state_machine_arn = stateMachine.stateMachineArn;
  }
}
