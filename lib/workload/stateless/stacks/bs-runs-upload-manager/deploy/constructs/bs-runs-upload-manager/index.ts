import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { IRole } from 'aws-cdk-lib/aws-iam';
import { PythonLambdaLayerConstruct } from '../../../../../../components/python-lambda-layer';

interface BsRunsUploadManagerConstructProps {
  /* Stack objects */
  lambdaLayerObj: PythonLambdaLayerConstruct;
  icaTokenSecretObj: secretsManager.ISecret;
  portalTokenSecretObj: secretsManager.ISecret;
  basespaceSecretObj: secretsManager.ISecret;
  dataPortalApiUrlSsmParameterObj: ssm.IStringParameter;
  eventBusObj: events.IEventBus;
  /* Lambda layer paths */
  uploadV2SamplesheetToGdsBsshLambdaPath: string; // __dirname + '/../../../lambdas/upload_v2_samplesheet_to_gds_bssh'
  launchBsRunsUploadTesLambdaPath: string; // __dirname + '/../../../lambdas/launch_bs_runs_upload_tes'
  /* Step function templates */
  gdsSystemFilesPath: string; // gds://development/primary_data/temp/bs_runs_upload_tes/
  /* Miscell */
  workflowDefinitionBodyPath: string; // __dirname + '/../../../step_functions_templates/bs_runs_upload_step_functions_template.json'
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
        entry: props.uploadV2SamplesheetToGdsBsshLambdaPath,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdaLayerObj.lambdaLayerVersionObj],
        timeout: Duration.seconds(60),
        environment: {
          ICA_BASE_URL: 'https://aps2.platform.illumina.com',
          ICA_ACCESS_TOKEN_SECRET_ID: props.icaTokenSecretObj.secretName,
          PORTAL_API_URL_PARAMETER_NAME: props.dataPortalApiUrlSsmParameterObj.parameterName,
          PORTAL_TOKEN_SECRET_ID: props.portalTokenSecretObj.secretName,
        },
      }
    );

    // Launch BS Runs Upload TES lambda
    const launch_bs_runs_upload_tes_lambda = new PythonFunction(
      this,
      'launch_bs_runs_upload_tes_lambda',
      {
        entry: props.launchBsRunsUploadTesLambdaPath,
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [props.lambdaLayerObj.lambdaLayerVersionObj],
        timeout: Duration.seconds(60),
        environment: {
          BASESPACE_API_SERVER: 'https://api.aps2.sh.basespace.illumina.com',
          BASESPACE_ACCESS_TOKEN_SECRET_ID: props.basespaceSecretObj.secretName,
          ICA_BASE_URL: 'https://aps2.platform.illumina.com',
          ICA_ACCESS_TOKEN_SECRET_ID: props.icaTokenSecretObj.secretName,
          GDS_SYSTEM_FILES_PATH: props.gdsSystemFilesPath,
        },
      }
    );

    // Give the lambda permission to read the ICA ACCESS TOKEN secret
    [launch_bs_runs_upload_tes_lambda, upload_v2_samplesheet_to_gds_bssh_lambda].forEach(
      (lambda_obj) => {
        props.icaTokenSecretObj.grantRead(<IRole>lambda_obj.role);
        props.portalTokenSecretObj.grantRead(<IRole>lambda_obj.role);
      }
    );

    // Give the lambda permission to read the PORTAL TOKEN secret
    props.portalTokenSecretObj.grantRead(<IRole>upload_v2_samplesheet_to_gds_bssh_lambda.role);

    // Give the lambda permission to read the ssm parameter value of the data portal api url
    props.dataPortalApiUrlSsmParameterObj.grantRead(
      <IRole>upload_v2_samplesheet_to_gds_bssh_lambda.role
    );

    // Give basespace upload lambda permission to read the basespace access token secret
    props.basespaceSecretObj.grantRead(<IRole>launch_bs_runs_upload_tes_lambda.role);

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'bs_runs_upload_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflowDefinitionBodyPath),
      // definitionSubstitutions
      definitionSubstitutions: {
        __upload_v2_samplesheet_to_gds_bssh_function_arn__:
          upload_v2_samplesheet_to_gds_bssh_lambda.currentVersion.functionArn,
        __launch_bs_runs_upload_tes_function_arn__:
          launch_bs_runs_upload_tes_lambda.currentVersion.functionArn,
      },
    });

    // Add execution permissions to stateMachine role
    [upload_v2_samplesheet_to_gds_bssh_lambda, launch_bs_runs_upload_tes_lambda].forEach(
      (lambda_obj) => {
        lambda_obj.currentVersion.grantInvoke(stateMachine.role);
      }
    );

    // Trigger state machine on event
    const rule = new events.Rule(this, 'bs_runs_upload_event_rule', {
      eventBus: props.eventBusObj,
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
