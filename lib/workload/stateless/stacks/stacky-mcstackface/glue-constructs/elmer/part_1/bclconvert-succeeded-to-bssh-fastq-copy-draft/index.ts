import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
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
* Input Event WorkflowRunName: bclconvert
* Input Event status: `succeeded`


* Output Event source: `orcabus.bsshfastqcopyinputeventglue`
* Output Event DetailType: `WorkflowDraftRunStateChange`
* Output Event status: `draft`


* The BCLConvertSuccededToBsshFastqCopyDraft Construct
  * Subscribes to the BCLConvertManagerEventHandler Stack outputs and creates the input for the BSSHFastqCopyManager
  * Pushes an event payload of the input for the BCLConvertSuccededToBsshFastqCopyDraft Construct

*/

export interface bsshFastqCopyManagerDraftMakerConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class BsshFastqCopyManagerDraftMakerConstruct extends Construct {
  public readonly bsshFastqCopyManagerDraftMakerEventMap = {
    prefix: 'bclConvertToBsshFastqCopyDraft',
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bclconvert',
    outputSource: 'orcabus.bsshfastqcopyinputeventglue',
    outputDetailType: 'WorkflowDraftRunStateChange',
    outputStatus: 'draft',
    payloadVersion: '2024.05.24',
    workflowName: 'bsshFastqCopy',
    workflowVersion: '2024.05.24',
  };

  constructor(scope: Construct, id: string, props: bsshFastqCopyManagerDraftMakerConstructProps) {
    super(scope, id);

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfn_preamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.bsshFastqCopyManagerDraftMakerEventMap.prefix}_sfn_preamble`,
      {
        portalRunTablePartitionName:
          this.bsshFastqCopyManagerDraftMakerEventMap.portalRunPartitionName,
        stateMachinePrefix: this.bsshFastqCopyManagerDraftMakerEventMap.prefix,
        tableObj: props.tableObj,
        workflowName: this.bsshFastqCopyManagerDraftMakerEventMap.workflowName,
        workflowVersion: this.bsshFastqCopyManagerDraftMakerEventMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const draftMakerSfn = new sfn.StateMachine(this, 'bclconvert_succeeded_to_bssh_draft', {
      stateMachineName: `${this.bsshFastqCopyManagerDraftMakerEventMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'bclconvert_succeeded_to_bssh_fastq_copy_draft_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        // Event stuff
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.bsshFastqCopyManagerDraftMakerEventMap.outputSource,
        __detail_type__: this.bsshFastqCopyManagerDraftMakerEventMap.outputDetailType,
        // Workflow stuff
        __workflow_name__: this.bsshFastqCopyManagerDraftMakerEventMap.workflowName,
        __workflow_version__: this.bsshFastqCopyManagerDraftMakerEventMap.workflowVersion,
        __payload_version__: this.bsshFastqCopyManagerDraftMakerEventMap.payloadVersion,
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
