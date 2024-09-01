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

Output Event Source: `orcabus.umccriseinputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `draft`

* Subscribe to the workflow manager succeeded event for tumor normal libraries.
* Launch a draft event for the umccrise pipeline
*/

export interface TnCompleteToUmccriseDraftConstructProps {
  eventBusObj: events.IEventBus;
  tableObj: dynamodb.ITableV2;
  workflowsTableObj: dynamodb.ITableV2;
}

export class TnCompleteToUmccriseDraftConstruct extends Construct {
  public readonly UmccriseDraftMap = {
    prefix: 'pva-tn-complete-to-umccrise-draft',
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerWorkflowName: 'tumor_normal',
    triggerDetailType: 'WorkflowRunStateChange',
    outputSource: 'orcabus.umccriseinputeventglue',
    outputDetailType: 'WorkflowDraftRunStateChange',
    outputStatus: 'DRAFT',
    payloadVersion: '2024.07.23',
    workflowName: 'umccrise',
    workflowVersion: '2.3.1',
    tablePartitionName: 'subject',
  };

  constructor(scope: Construct, id: string, props: TnCompleteToUmccriseDraftConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_draft_event_payload_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_draft_event_payload_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_draft_event_payload.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfn_preamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.UmccriseDraftMap.prefix}_sfn_preamble`,
      {
        portalRunTablePartitionName: this.UmccriseDraftMap.portalRunPartitionName,
        stateMachinePrefix: this.UmccriseDraftMap.prefix,
        tableObj: props.workflowsTableObj,
        workflowName: this.UmccriseDraftMap.workflowName,
        workflowVersion: this.UmccriseDraftMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const qcCompleteToDraftSfn = new sfn.StateMachine(this, 'tn_complete_to_umccrise_draft_sfn', {
      stateMachineName: `${this.UmccriseDraftMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'tn_complete_to_umccrise_draft_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Events */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.UmccriseDraftMap.outputSource,
        __detail_type__: this.UmccriseDraftMap.outputDetailType,
        __output_status__: this.UmccriseDraftMap.outputStatus,
        __payload_version__: this.UmccriseDraftMap.payloadVersion,
        __workflow_name__: this.UmccriseDraftMap.workflowName,
        __workflow_version__: this.UmccriseDraftMap.workflowVersion,

        /* Lambdas */
        __generate_draft_event_payload_lambda_function_arn__:
          generateEventDataLambdaObj.currentVersion.functionArn,

        /* Tables */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __subject_table_partition_name__: this.UmccriseDraftMap.tablePartitionName,

        // State Machines
        __sfn_preamble_state_machine_arn__: sfn_preamble.stateMachineArn,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(qcCompleteToDraftSfn);

    // allow the step function to submit events
    props.eventBusObj.grantPutEventsTo(qcCompleteToDraftSfn);

    // allow the step function to invoke the lambdas
    generateEventDataLambdaObj.currentVersion.grantInvoke(qcCompleteToDraftSfn);

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    qcCompleteToDraftSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );
    // Allow the state machine to be able to invoke the preamble sfn
    sfn_preamble.grantStartExecution(qcCompleteToDraftSfn);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'tn_complete_to_umccrise_draft_rule', {
      ruleName: `stacky-${this.UmccriseDraftMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.UmccriseDraftMap.triggerSource],
        detailType: [this.UmccriseDraftMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.UmccriseDraftMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.UmccriseDraftMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(qcCompleteToDraftSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
