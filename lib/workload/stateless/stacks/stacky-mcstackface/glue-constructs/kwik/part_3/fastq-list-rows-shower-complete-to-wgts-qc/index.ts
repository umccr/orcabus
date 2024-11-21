import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { GenerateWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/sfn-generate-workflowrunstatechange-ready-event';
import { NagSuppressions } from 'cdk-nag';

/*
Part 3

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `FastqListRowStateChange`
Input Event status: `FastqListRowEventShowerComplete`

Output Event source: `orcabus.wgtsinputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `READY`

* Trigger wgts events collecting all wgts in the run
*/

export interface WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps {
  /* Event Bus Object */
  eventBusObj: events.IEventBus;

  /* DynamoDB Table */
  wgtsQcGlueTableObj: dynamodb.ITableV2;

  /* SSM Param objects */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class WgtsQcFastqListRowShowerCompleteToWorkflowReadyConstruct extends Construct {
  public readonly WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap = {
    /* General settings */
    prefix: 'kwik-fqlr-shower-to-wgts-qc',
    /* Table Partition Settings */
    wgtsGlueTablePartition: {
      library: 'library',
      fastqListRow: 'fastq_list_row',
    },
    portalRunPartitionName: 'portal_run',
    /* Input Event Settings */
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'FastqListRowEventShowerComplete',
    triggerDetailType: 'FastqListRowShowerStateChange',
    /* Output Source */
    outputSource: 'orcabus.wgtsqcinputeventglue',
    /* Payload version */
    payloadVersion: '0.1.0',
    /* Workflow settings */
    workflowName: 'wgts-qc',
    workflowVersion: '4.2.4',
  };

  constructor(
    scope: Construct,
    id: string,
    props: WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix,
        workflowName: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
        workflowVersion:
          this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the lambdas
    */
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_event_data', {
      entry: path.join(__dirname, 'lambdas', 'generate_event_data_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_event_data.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 3: Build the engine parameters sfn
    */
    const engineParameterAndReadyEventMakerSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'fastqlistrow_complete_to_wgtsqc_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputSource,
        payloadVersion:
          this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.payloadVersion,
        workflowName: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
        workflowVersion:
          this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Prefixes */
        lambdaPrefix: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix,
        stateMachinePrefix: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 4: Build the inputs sfn
    */
    const inputMakerSfn = new sfn.StateMachine(
      this,
      'fastq_list_row_complete_to_workflow_draft_run_events',
      {
        stateMachineName: `${this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'fastq_list_rows_shower_complete_to_wgts_qc_draft_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* General Settings */
          __event_bus_name__: props.eventBusObj.eventBusName,
          __table_name__: props.wgtsQcGlueTableObj.tableName,

          /* Table partitions */
          __fastq_list_row_partition_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.wgtsGlueTablePartition
              .fastqListRow,
          __library_partition_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.wgtsGlueTablePartition
              .library,
          __portal_run_partition_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.portalRunPartitionName,
          /* Output event settings */
          // Workflow detail
          __workflow_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
          __workflow_version__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,

          /* Lambdas */
          __generate_wgts_draft_event_data_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,

          /* Nested sfn */
          __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
          __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
        },
      }
    );

    /*
    Part 3: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.wgtsQcGlueTableObj.grantReadWriteData(inputMakerSfn);

    // Allow the sfn to invoke the lambda
    generateEventDataLambdaObj.currentVersion.grantInvoke(inputMakerSfn);

    // Allow the state machine to be able to invoke the preamble sfn
    [sfnPreamble, engineParameterAndReadyEventMakerSfn].forEach((sfnObj) => {
      sfnObj.grantStartExecution(inputMakerSfn);
      sfnObj.grantRead(inputMakerSfn);
    });

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    inputMakerSfn.addToRolePolicy(
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
      inputMakerSfn,
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
    Part 4: Subscribe to the event bus for this event type
    */
    const rule = new events.Rule(this, 'wgts_subscribe_to_fastq_list_row_shower_complete', {
      ruleName: `stacky-${this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerSource],
        detailType: [
          this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerDetailType,
        ],
        detail: {
          status: [
            {
              'equals-ignore-case':
                this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerStatus,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(inputMakerSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
