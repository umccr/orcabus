import { Construct } from 'constructs';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { GenerateWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/sfn-generate-workflowrunstatechange-ready-event';
import { NagSuppressions } from 'cdk-nag';

/*
Part 1

* Input Event Source: `orcabus.workflowmanager`
* Input Event DetailType: `WorkflowRunStateChange`
* Input Event WorkflowName: bsshFastqCopy
* Input Event status: `succeeded`


* Output Event source: `orcabus.bclconvertinteropqcinputeventglue`
* Output Event DetailType: `WorkflowDraftRunStateChange`
* Output Event status: `draft`


* The BsshFastqCopySucceededToBclconvertInteropQcDraft Construct
  * Subscribes to the Workflow Manager for any workflow name called 'bsshFastqCopy'
  * Collects the outputs from the BsshFastqCopy workflow and pushes them to the BclconvertInteropQc workflow as a draft
  * Pushes an event payload of the input for the BCLConvertSuccededToBsshFastqCopyDraft Construct

*/

export interface bclconvertInteropQcDraftMakerConstructProps {
  /* Event Bus */
  eventBusObj: events.IEventBus;
  /* SSM Parameter Objects */
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class BclconvertInteropQcDraftMakerConstruct extends Construct {
  public readonly bclconvertInteropQcDraftMakerEventMap = {
    prefix: 'gorilla-bssh-fq-to-interop-qc',
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bsshFastqCopy',
    outputSource: 'orcabus.bclconvertinteropqcinputeventglue',
    payloadVersion: '2024.05.24',
    workflowName: 'bclconvert-interop-qc',
    workflowVersion: '2024.05.24',
  };

  constructor(scope: Construct, id: string, props: bclconvertInteropQcDraftMakerConstructProps) {
    super(scope, id);

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.bclconvertInteropQcDraftMakerEventMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.bclconvertInteropQcDraftMakerEventMap.prefix,
        workflowName: this.bclconvertInteropQcDraftMakerEventMap.workflowName,
        workflowVersion: this.bclconvertInteropQcDraftMakerEventMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the engine parameters sfn
    */
    const engineParametersAndReadyLaunchSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'bssh_copy_complete_to_bclconvert_interop_qc_ready_ep_sfn',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.bclconvertInteropQcDraftMakerEventMap.outputSource,
        payloadVersion: this.bclconvertInteropQcDraftMakerEventMap.payloadVersion,
        workflowName: this.bclconvertInteropQcDraftMakerEventMap.workflowName,
        workflowVersion: this.bclconvertInteropQcDraftMakerEventMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Prefixes */
        lambdaPrefix: this.bclconvertInteropQcDraftMakerEventMap.prefix,
        stateMachinePrefix: this.bclconvertInteropQcDraftMakerEventMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const inputsMakerSfn = new sfn.StateMachine(this, 'bssh_complete_to_bclconvert_sfn', {
      stateMachineName: `${this.bclconvertInteropQcDraftMakerEventMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'generate_bclconvert_interop_qc_draft_event_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        // Workflow stuff
        __workflow_name__: this.bclconvertInteropQcDraftMakerEventMap.workflowName,
        __workflow_version__: this.bclconvertInteropQcDraftMakerEventMap.workflowVersion,
        __payload_version__: this.bclconvertInteropQcDraftMakerEventMap.payloadVersion,
        // Subfunctions
        __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
        __launch_ready_event_sfn_arn__: engineParametersAndReadyLaunchSfn.stateMachineArn,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    [sfnPreamble, engineParametersAndReadyLaunchSfn].forEach((sfnObj) => {
      sfnObj.grantStartExecution(inputsMakerSfn);
      sfnObj.grantRead(inputsMakerSfn);
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

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      inputsMakerSfn,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    /*
    Part 3: Subscribe to the event bus for this event type
    */
    const rule = new events.Rule(this, 'bclconvert_interop_qc_subscribe_to_bssh_fastq_copy_event', {
      ruleName: `stacky-${this.bclconvertInteropQcDraftMakerEventMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.bclconvertInteropQcDraftMakerEventMap.triggerSource],
        detailType: [this.bclconvertInteropQcDraftMakerEventMap.triggerDetailType],
        detail: {
          status: [
            {
              'equals-ignore-case': this.bclconvertInteropQcDraftMakerEventMap.triggerStatus,
            },
          ],
          workflowName: [
            {
              'equals-ignore-case': this.bclconvertInteropQcDraftMakerEventMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(inputsMakerSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
