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
Part 4

Input Event Source: `orcabus.fastqglue`
Input Event DetailType: `FastqListRowShowerStateChange`
Input Event status: `FastqListRowEventShowerComplete`

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `READY`

* Trigger cttsov2 events collecting all cttsov2 in the run
*/

export interface Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps {
  /* Event Obj */
  eventBusObj: events.IEventBus;

  /* Tables */
  cttsov2GlueTableObj: dynamodb.ITableV2;

  /* SSM Parameters */
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;

  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class Cttsov2FastqListRowShowerCompleteToWorkflowDraftConstruct extends Construct {
  public readonly Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap = {
    /* General settings */
    prefix: 'jbweld-fqlr-shower-to-cttsov2',
    /* Table Partition Settings */
    cttsov2GlueTablePartition: {
      library: 'library',
      bclconvertData: 'bclconvert_data',
      fastqListRow: 'fastq_list_row',
    },
    portalRunPartitionName: 'portal_run', // For workflow table
    /* Input Event Settings */
    triggerSource: 'orcabus.fastqglue',
    triggerStatus: 'FastqListRowEventShowerComplete',
    triggerDetailType: 'FastqListRowShowerStateChange',
    /* Output Event Settings */
    outputSource: 'orcabus.cttsov2inputeventglue',
    outputStatus: 'DRAFT',
    outputDetailType: 'WorkflowDraftRunStateChange',
    /* Payload version */
    payloadVersion: '0.1.0',
    /* Workflow settings */
    workflowName: 'cttsov2',
    workflowVersion: '2.6.0',
  };

  constructor(
    scope: Construct,
    id: string,
    props: Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    const buildCttsoV2Samplesheet = new PythonFunction(this, 'build_cttsov2_samplesheet', {
      entry: path.join(__dirname, 'lambdas', 'build_cttsov2_samplesheet_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'build_cttso_v2_samplesheet.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix,
        workflowName: this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
        workflowVersion:
          this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the engine parameters sfn
    */
    const engineParameterAndReadyEventMakerSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'fastqlistrow_complete_to_cttsov2_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputSource,
        payloadVersion:
          this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.payloadVersion,
        workflowName: this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
        workflowVersion:
          this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Prefixes */
        lambdaPrefix: this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix,
        stateMachinePrefix: this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 3: Build the sfn
    */
    const inputMakerSfn = new sfn.StateMachine(
      this,
      'fastq_list_row_complete_to_workflow_draft_run_events',
      {
        stateMachineName: `${this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'fastq_list_row_shower_complete_event_to_cttsov2_draft_events_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* General Settings */
          __event_bus_name__: props.eventBusObj.eventBusName,
          __table_name__: props.cttsov2GlueTableObj.tableName,

          /* Table partitions */
          __bclconvert_data_row_partition_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap
              .cttsov2GlueTablePartition.bclconvertData,
          __fastq_list_row_partition_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap
              .cttsov2GlueTablePartition.fastqListRow,
          __library_partition_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap
              .cttsov2GlueTablePartition.library,

          /* Output event settings */
          // Event detail
          __event_source__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputSource,
          __detail_type__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputDetailType,
          __output_status__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputStatus,
          __payload_version__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.payloadVersion,
          // Workflow detail
          __workflow_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
          __workflow_version__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,

          /* Lambdas */
          __generate_samplesheet_lambda_function_arn__:
            buildCttsoV2Samplesheet.currentVersion.functionArn,

          /* Subfunctions */
          __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
          __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
        },
      }
    );

    /*
    Part 3: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.cttsov2GlueTableObj.grantReadWriteData(inputMakerSfn);

    // Allow the sfn to invoke the lambda
    buildCttsoV2Samplesheet.currentVersion.grantInvoke(inputMakerSfn);

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
    const rule = new events.Rule(this, 'cttsov2_subscribe_to_fastq_list_row_shower_complete', {
      ruleName: `stacky-${this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerSource],
        detailType: [
          this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerDetailType,
        ],
        detail: {
          status: [
            {
              'equals-ignore-case':
                this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerStatus,
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
