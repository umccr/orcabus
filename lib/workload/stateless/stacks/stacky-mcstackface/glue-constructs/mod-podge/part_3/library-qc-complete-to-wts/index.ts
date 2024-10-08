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
import { GetMetadataLambdaConstruct } from '../../../../../../../components/python-lambda-metadata-mapper';

/*
Part 4

Input Event Source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: `LibraryStateChange`
Input Event status: `QcComplete`

Output Event Source: `orcabus.wtsinputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `draft`

* Subscribe to the wgts input event glue, library complete event.
* Launch a draft event for the wts pipeline if the libraries' subject has a complement library that is also complete
*/

export interface LibraryQcCompleteToWtsDraftConstructProps {
  /* Events */
  eventBusObj: events.IEventBus;
  /* Tables */
  tableObj: dynamodb.ITableV2;
  /* SSM */
  outputUriSsmParameterObj: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class LibraryQcCompleteToWtsReadyConstruct extends Construct {
  public readonly WtsReadyMap = {
    prefix: 'modpodge-library-qc-to-wts',
    tablePartition: {
      library: 'library',
      fastq_list_row: 'fastq_list_row',
    },
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'QC_COMPLETE',
    triggerDetailType: 'LibraryStateChange',
    outputSource: 'orcabus.wtsinputeventglue',
    payloadVersion: '2024.07.23',
    workflowName: 'wts',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: LibraryQcCompleteToWtsDraftConstructProps) {
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
      `${this.WtsReadyMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.WtsReadyMap.prefix,
        workflowName: this.WtsReadyMap.workflowName,
        workflowVersion: this.WtsReadyMap.workflowVersion,
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
        outputSource: this.WtsReadyMap.outputSource,
        payloadVersion: this.WtsReadyMap.payloadVersion,
        workflowName: this.WtsReadyMap.workflowName,
        workflowVersion: this.WtsReadyMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Prefixes */
        lambdaPrefix: this.WtsReadyMap.prefix,
        stateMachinePrefix: this.WtsReadyMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const qcCompleteToDraftSfn = new sfn.StateMachine(
      this,
      'library_qc_complete_sfn_to_wts_draft',
      {
        stateMachineName: `${this.WtsReadyMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'add_library_qc_complete_to_wts_draft_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Lambdas */
          __generate_draft_event_payload_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,

          /* Tables */
          __table_name__: props.tableObj.tableName,
          __library_partition_name__: this.WtsReadyMap.tablePartition.library,
          __fastq_list_row_partition_name__: this.WtsReadyMap.tablePartition.fastq_list_row,

          /* State Machines */
          __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
          __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
        },
      }
    );

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(qcCompleteToDraftSfn);

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
    sfnPreamble.grantStartExecution(qcCompleteToDraftSfn);
    engineParameterAndReadyEventMakerSfn.grantStartExecution(qcCompleteToDraftSfn);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'library_qc_complete_to_tn_draft', {
      ruleName: `stacky-${this.WtsReadyMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WtsReadyMap.triggerSource],
        detailType: [this.WtsReadyMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.WtsReadyMap.triggerStatus }],
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
