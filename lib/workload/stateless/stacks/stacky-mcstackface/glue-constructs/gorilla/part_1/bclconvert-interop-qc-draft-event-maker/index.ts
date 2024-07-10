import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';

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
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class BclconvertInteropQcDraftMakerConstruct extends Construct {
  public readonly bclconvertInteropQcDraftMakerEventMap = {
    prefix: 'bsshFastqCompleteToBclconvertInteropQcDraft',
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bsshFastqCopy',
    outputSource: 'orcabus.bclconvertinteropqcinputeventglue',
    outputDetailType: 'WorkflowDraftRunStateChange',
    outputStatus: 'draft',
    payloadVersion: '2024.05.24',
    workflowName: 'bclconvertInteropQc',
    workflowVersion: '2024.05.24',
  };

  constructor(scope: Construct, id: string, props: bclconvertInteropQcDraftMakerConstructProps) {
    super(scope, id);

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfn_preamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.bclconvertInteropQcDraftMakerEventMap.prefix}_sfn_preamble`,
      {
        portalRunTablePartitionName:
          this.bclconvertInteropQcDraftMakerEventMap.portalRunPartitionName,
        stateMachinePrefix: this.bclconvertInteropQcDraftMakerEventMap.prefix,
        tableObj: props.tableObj,
        workflowName: this.bclconvertInteropQcDraftMakerEventMap.workflowName,
        workflowVersion: this.bclconvertInteropQcDraftMakerEventMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const draftMakerSfn = new sfn.StateMachine(this, 'bssh_complete_to_bclconvert_sfn', {
      stateMachineName: `${this.bclconvertInteropQcDraftMakerEventMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'generate_bclconvert_interop_qc_draft_event_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        // Event stuff
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.bclconvertInteropQcDraftMakerEventMap.outputSource,
        __detail_type__: this.bclconvertInteropQcDraftMakerEventMap.outputDetailType,
        // Workflow stuff
        __workflow_name__: this.bclconvertInteropQcDraftMakerEventMap.workflowName,
        __workflow_version__: this.bclconvertInteropQcDraftMakerEventMap.workflowVersion,
        __payload_version__: this.bclconvertInteropQcDraftMakerEventMap.payloadVersion,
        // Subfunctions
        __sfn_preamble_state_machine_arn__: sfn_preamble.stateMachineArn,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // Read/write to the table
    props.tableObj.grantReadWriteData(draftMakerSfn.role);

    // Allow the step function to submit events
    props.eventBusObj.grantPutEventsTo(draftMakerSfn.role);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    draftMakerSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Add state machine execution permissions to stateMachine role
    sfn_preamble.grantStartExecution(draftMakerSfn.role);
  }
}
