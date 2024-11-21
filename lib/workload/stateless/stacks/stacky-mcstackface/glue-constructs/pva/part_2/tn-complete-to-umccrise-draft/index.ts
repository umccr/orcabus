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
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';
import { GenerateWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/sfn-generate-workflowrunstatechange-ready-event';
import { NagSuppressions } from 'cdk-nag';

/*
Part 2

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event WorkflowName: tumor-normal
Input Event status: `SUCCEEDED`

Output Event Source: `orcabus.umccriseinputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `READY`

* Subscribe to the workflow manager succeeded event for tumor normal libraries.
* Launch a draft event for the umccrise pipeline
*/

export interface TnCompleteToUmccriseDraftConstructProps {
  /* Events */
  eventBusObj: events.IEventBus;
  /* Tables */
  tableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  outputUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class TnCompleteToUmccriseReadyConstruct extends Construct {
  public readonly UmccriseReadyMap = {
    prefix: 'pva-tn-complete-to-umccrise',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerWorkflowName: 'tumor-normal',
    triggerDetailType: 'WorkflowRunStateChange',
    outputSource: 'orcabus.umccriseinputeventglue',
    payloadVersion: '2024.07.23',
    workflowName: 'umccrise',
    workflowVersion: '2.3.1',
    tablePartitionName: 'library',
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
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.UmccriseReadyMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.UmccriseReadyMap.prefix,
        workflowName: this.UmccriseReadyMap.workflowName,
        workflowVersion: this.UmccriseReadyMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the engine parameters sfn
    */
    const engineParameterAndReadyEventMakerSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'fastqlistrow_complete_to_wgtsqc_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.UmccriseReadyMap.outputSource,
        payloadVersion: this.UmccriseReadyMap.payloadVersion,
        workflowName: this.UmccriseReadyMap.workflowName,
        workflowVersion: this.UmccriseReadyMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Prefixes */
        lambdaPrefix: this.UmccriseReadyMap.prefix,
        stateMachinePrefix: this.UmccriseReadyMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const qcCompleteToDraftSfn = new sfn.StateMachine(this, 'tn_complete_to_umccrise_draft_sfn', {
      stateMachineName: `${this.UmccriseReadyMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'tn_complete_to_umccrise_draft_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __generate_draft_event_payload_lambda_function_arn__:
          generateEventDataLambdaObj.currentVersion.functionArn,

        /* Tables */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __library_partition_name__: this.UmccriseReadyMap.tablePartitionName,

        // State Machines
        __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
        __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(qcCompleteToDraftSfn);

    // allow the step function to invoke the lambdas
    generateEventDataLambdaObj.currentVersion.grantInvoke(qcCompleteToDraftSfn);

    // Allow the state machine to be able to invoke the preamble sfn
    [sfnPreamble, engineParameterAndReadyEventMakerSfn].forEach((sfnObj) => {
      sfnObj.grantStartExecution(qcCompleteToDraftSfn);
      sfnObj.grantRead(qcCompleteToDraftSfn);
    });

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

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      qcCompleteToDraftSfn,
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
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'tn_complete_to_umccrise_draft_rule', {
      ruleName: `stacky-${this.UmccriseReadyMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.UmccriseReadyMap.triggerSource],
        detailType: [this.UmccriseReadyMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.UmccriseReadyMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.UmccriseReadyMap.triggerWorkflowName,
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
