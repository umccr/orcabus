import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';

/*
Part 4

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event WorkflowName: tumor_normal
Input Event status: `succeeded`

Output Event Source: `orcabus.inputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `draft`

* Subscribe to the workflow manager succeeded event for tumor normal libraries.
* Launch a draft event for the
 pipeline
*/

export interface UmccriseAndWtsCompleteToRnasumDraftDraftConstructProps {
  eventBusObj: events.IEventBus;
  tableObj: dynamodb.ITableV2;
  workflowsTableObj: dynamodb.ITableV2;
}

export class UmccriseAndWtsCompleteToRnasumDraftDraftConstruct extends Construct {
  public readonly RnasumDraftMap = {
    prefix: 'roket-umccrise-wts-complete-to-rnasum-draft',
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerWorkflowName: {
      wts: 'wts',
      umccrise: 'umccrise',
    },
    successWorkflowStatus: 'SUCCEEDED',
    wtsWorkflowName: 'wts',
    triggerDetailType: 'WorkflowRunStateChange',
    tablePartitions: {
      subject: 'subject',
    },
    outputSource: 'orcabus.rnasuminputeventglue',
    outputDetailType: 'WorkflowDraftRunStateChange',
    outputStatus: 'DRAFT',
    payloadVersion: '2024.07.23',
    workflowName: 'rnasum',
    workflowVersion: '4.2.4',
  };

  constructor(
    scope: Construct,
    id: string,
    props: UmccriseAndWtsCompleteToRnasumDraftDraftConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_workflow_inputs_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_workflow_inputs_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_workflow_inputs.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfn_preamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.RnasumDraftMap.prefix}_sfn_preamble`,
      {
        portalRunTablePartitionName: this.RnasumDraftMap.portalRunPartitionName,
        stateMachinePrefix: this.RnasumDraftMap.prefix,
        tableObj: props.workflowsTableObj,
        workflowName: this.RnasumDraftMap.workflowName,
        workflowVersion: this.RnasumDraftMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const umccriseAndWtsCompleteToDraftSfn = new sfn.StateMachine(
      this,
      'umccrise_and_wts_complete_to_rnasum_draft_sfn',
      {
        stateMachineName: `${this.RnasumDraftMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'umccrise_and_wts_complete_to_rnasum_draft.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Events */
          __event_bus_name__: props.eventBusObj.eventBusName,
          __event_source__: this.RnasumDraftMap.outputSource,
          __detail_type__: this.RnasumDraftMap.outputDetailType,
          __output_status__: this.RnasumDraftMap.outputStatus,
          __payload_version__: this.RnasumDraftMap.payloadVersion,
          __workflow_name__: this.RnasumDraftMap.workflowName,
          __workflow_version__: this.RnasumDraftMap.workflowVersion,

          /* Lambdas */
          __generate_workflow_inputs_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,

          /* Tables */
          __table_name__: props.tableObj.tableName,

          /* Table partitions */
          __subject_table_partition_name__: this.RnasumDraftMap.tablePartitions.subject,

          /* Statuses */
          __success_workflow_status__: this.RnasumDraftMap.successWorkflowStatus,

          /* WTS Workflow status */
          __wts_workflow_name__: this.RnasumDraftMap.wtsWorkflowName,

          // State Machines
          __sfn_preamble_state_machine_arn__: sfn_preamble.stateMachineArn,
        },
      }
    );

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(umccriseAndWtsCompleteToDraftSfn);

    // allow the step function to submit events
    props.eventBusObj.grantPutEventsTo(umccriseAndWtsCompleteToDraftSfn);

    // allow the step function to invoke the lambdas
    generateEventDataLambdaObj.currentVersion.grantInvoke(umccriseAndWtsCompleteToDraftSfn);

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    umccriseAndWtsCompleteToDraftSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );
    // Allow the state machine to be able to invoke the preamble sfn
    sfn_preamble.grantStartExecution(umccriseAndWtsCompleteToDraftSfn);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'umccrise_and_wts_to_rnasum_draft_rule', {
      ruleName: `stacky-${this.RnasumDraftMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.RnasumDraftMap.triggerSource],
        detailType: [this.RnasumDraftMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.RnasumDraftMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.RnasumDraftMap.triggerWorkflowName.umccrise,
            },
            {
              'equals-ignore-case': this.RnasumDraftMap.triggerWorkflowName.wts,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(umccriseAndWtsCompleteToDraftSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
