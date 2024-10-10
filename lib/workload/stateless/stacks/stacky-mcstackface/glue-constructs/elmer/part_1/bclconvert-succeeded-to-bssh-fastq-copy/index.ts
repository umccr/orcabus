import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { LambdaB64GzTranslatorConstruct } from '../../../../../../../components/python-lambda-b64gz-translator';
import { GetLibraryObjectsFromSamplesheetConstruct } from '../../../../../../../components/python-lambda-get-metadata-objects-from-samplesheet';
import { GenerateWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/sfn-generate-workflowrunstatechange-ready-event';

/*
Part 1

* Input Event Source: `orcabus.workflowmanager`
* Input Event DetailType: `WorkflowRunStateChange`
* Input Event WorkflowRunName: bclconvert
* Input Event status: `succeeded`


* Output Event source: `orcabus.bsshfastqcopyinputeventglue`
* Output Event DetailType: `WorkflowRunStateChange`
* Output Event status: `READY`


* The BCLConvertSucceededToBsshFastqCopyDraft Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
  * Pushes an event payload of the input for the BCLConvertSuccededToBsshFastqCopyDraft Construct

*/

export interface bsshFastqCopyManagerDraftMakerConstructProps {
  /* Event bus object handler */
  eventBusObj: events.IEventBus;
  /* SSM Parameter for the output uri */
  outputUriSsmParameterObj: ssm.IStringParameter;
  /* Secret for icav2 access token */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class BsshFastqCopyManagerReadyMakerConstruct extends Construct {
  public readonly bsshFastqCopyManagerDraftMakerEventMap = {
    prefix: 'elmer-bclconv-2-bssh-fq-copy',
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bclconvert',
    outputSource: 'orcabus.bsshfastqcopyinputeventglue',
    payloadVersion: '2024.05.24',
    workflowName: 'bsshFastqCopy',
    workflowVersion: '2024.05.24',
  };

  constructor(scope: Construct, id: string, props: bsshFastqCopyManagerDraftMakerConstructProps) {
    super(scope, id);

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.bsshFastqCopyManagerDraftMakerEventMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.bsshFastqCopyManagerDraftMakerEventMap.prefix,
        workflowName: this.bsshFastqCopyManagerDraftMakerEventMap.workflowName,
        workflowVersion: this.bsshFastqCopyManagerDraftMakerEventMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 1a: Build the lambdas
    */
    // Decompression lambda
    const decompressSamplesheetLambda = new LambdaB64GzTranslatorConstruct(
      this,
      'lambda_b64gz_translator_lambda',
      {
        functionNamePrefix: this.bsshFastqCopyManagerDraftMakerEventMap.prefix,
      }
    ).lambdaObj;

    // Get all libraries from samplesheet lambda
    const getLibrarySubjectMapLambda = new GetLibraryObjectsFromSamplesheetConstruct(
      this,
      'get_library_subject_map_lambda',
      {
        functionNamePrefix: this.bsshFastqCopyManagerDraftMakerEventMap.prefix,
      }
    ).lambdaObj;

    /*
    Part 2: Build the engine parameters sfn through the construct
    */
    const engineParametersAndReadyLaunchSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'bclconvert_succeeded_to_bssh_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.bsshFastqCopyManagerDraftMakerEventMap.outputSource,
        payloadVersion: this.bsshFastqCopyManagerDraftMakerEventMap.payloadVersion,
        workflowName: this.bsshFastqCopyManagerDraftMakerEventMap.workflowName,
        workflowVersion: this.bsshFastqCopyManagerDraftMakerEventMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Prefixes */
        lambdaPrefix: this.bsshFastqCopyManagerDraftMakerEventMap.prefix,
        stateMachinePrefix: this.bsshFastqCopyManagerDraftMakerEventMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the inputs sfn
    */
    const inputsMakerSfn = new sfn.StateMachine(this, 'bclconvert_succeeded_to_bssh_draft', {
      stateMachineName: `${this.bsshFastqCopyManagerDraftMakerEventMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'bclconvert_succeeded_to_bssh_fastq_copy_draft_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        // Subfunctions
        __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
        __launch_ready_event_sfn_arn__: engineParametersAndReadyLaunchSfn.stateMachineArn,
        // Lambda
        __decompression_samplesheet_lambda_function_arn__:
          decompressSamplesheetLambda.currentVersion.functionArn,
        __get_libraries_from_samplesheet_lambda_function_arn__:
          getLibrarySubjectMapLambda.currentVersion.functionArn,
      },
    });

    /*
    Part 2a: Grant the sfn permissions
    */

    // Allow the step function to launch the lambdas
    [decompressSamplesheetLambda, getLibrarySubjectMapLambda].forEach((lambda) => {
      lambda.currentVersion.grantInvoke(inputsMakerSfn);
    });

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    inputsMakerSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Add state machine execution permissions to stateMachine role
    sfnPreamble.grantStartExecution(inputsMakerSfn);
    engineParametersAndReadyLaunchSfn.grantStartExecution(inputsMakerSfn);

    const eventRule = new events.Rule(this, 'update_database_on_new_samplesheet_event_rule', {
      ruleName: `stacky-${this.bsshFastqCopyManagerDraftMakerEventMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.bsshFastqCopyManagerDraftMakerEventMap.triggerSource],
        detailType: [this.bsshFastqCopyManagerDraftMakerEventMap.triggerDetailType],
        detail: {
          status: [
            { 'equals-ignore-case': this.bsshFastqCopyManagerDraftMakerEventMap.triggerStatus },
          ],
          workflowName: [
            {
              'equals-ignore-case': this.bsshFastqCopyManagerDraftMakerEventMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target to event rule
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(inputsMakerSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
