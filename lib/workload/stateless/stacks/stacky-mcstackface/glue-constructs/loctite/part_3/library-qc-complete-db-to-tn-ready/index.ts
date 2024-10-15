import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';
import { GenerateWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/sfn-generate-workflowrunstatechange-ready-event';
import { GetMetadataLambdaConstruct } from '../../../../../../../components/python-lambda-metadata-mapper';

/*
Part 3

Input Event Source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: `LibraryStateChange`
Input Event status: `QcComplete`

Output Event Source: `orcabus.tninputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `draft`

* Subscribe to the wgts input event glue, library complete event. 
* Launch a draft event for the tumor normal pipeline if the libraries' subject has a complement library that is also complete
*/

export interface LibraryQcCompleteToTnDraftConstructProps {
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

export class LibraryQcCompleteToTnReadyConstruct extends Construct {
  public readonly TnReadyMap = {
    prefix: 'loctite-qc-complete-to-tn',
    tablePartition: {
      subject: 'subject',
      library: 'library',
      fastq_list_row: 'fastq_list_row',
    },
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'QC_COMPLETE',
    triggerDetailType: 'LibraryStateChange',
    outputSource: 'orcabus.tninputeventglue',
    payloadVersion: '2024.07.23',
    workflowName: 'tumor-normal',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: LibraryQcCompleteToTnDraftConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    const findComplementLibraryPair = new PythonFunction(this, 'find_complement_library_pair_py', {
      entry: path.join(__dirname, 'lambdas', 'find_complement_library_pair_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'find_complement_library_pair.py',
      handler: 'handler',
      memorySize: 1024,
    });

    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_draft_event_payload_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_draft_event_payload_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_draft_event_payload.py',
      handler: 'handler',
      memorySize: 1024,
    });

    // Generate the lambda to collect the orcabus id from the subject id
    const collectOrcaBusIdLambdaObj = new GetMetadataLambdaConstruct(
      this,
      'get_orcabus_id_from_subject_id',
      {
        functionNamePrefix: this.TnReadyMap.prefix,
      }
    ).lambdaObj;

    // Add CONTEXT, FROM_ID and RETURN_OBJ environment variables to the lambda
    collectOrcaBusIdLambdaObj.addEnvironment('CONTEXT', 'subject');
    collectOrcaBusIdLambdaObj.addEnvironment('FROM_ORCABUS', '');
    collectOrcaBusIdLambdaObj.addEnvironment('RETURN_OBJ', '');

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.TnReadyMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.TnReadyMap.prefix,
        workflowName: this.TnReadyMap.workflowName,
        workflowVersion: this.TnReadyMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the engineparameters event sfn
    */
    const engineParameterAndReadyEventMakerSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'fastqlistrow_complete_to_wgtsqc_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.TnReadyMap.outputSource,
        payloadVersion: this.TnReadyMap.payloadVersion,
        workflowName: this.TnReadyMap.workflowName,
        workflowVersion: this.TnReadyMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        icav2ProjectIdSsmParameterObj: props.icav2ProjectIdSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Secrets */
        icav2AccessTokenSecretObj: props.icav2AccessTokenSecretObj,

        /* Prefixes */
        lambdaPrefix: this.TnReadyMap.prefix,
        stateMachinePrefix: this.TnReadyMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'library_qc_complete_sfn_to_tn_draft', {
      stateMachineName: `${this.TnReadyMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'add_library_qc_complete_to_tn_draft_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __generate_draft_event_payload_lambda_function_arn__:
          generateEventDataLambdaObj.currentVersion.functionArn,
        __get_complement_library_pair_lambda_function_arn__:
          findComplementLibraryPair.currentVersion.functionArn,
        __get_orcabus_obj_from_subject_id_lambda_function_arn__:
          collectOrcaBusIdLambdaObj.currentVersion.functionArn,

        /* Tables */
        __table_name__: props.tableObj.tableName,
        __subject_partition_name__: this.TnReadyMap.tablePartition.subject,
        __library_partition_name__: this.TnReadyMap.tablePartition.library,
        __fastq_list_row_partition_name__: this.TnReadyMap.tablePartition.fastq_list_row,

        // State Machines
        __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
        __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn);

    // allow the step function to invoke the lambdas
    [generateEventDataLambdaObj, findComplementLibraryPair, collectOrcaBusIdLambdaObj].forEach(
      (lambdaObj) => {
        lambdaObj.currentVersion.grantInvoke(inputMakerSfn);
      }
    );

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
    // Allow the state machine to be able to invoke the preamble sfn
    sfnPreamble.grantStartExecution(inputMakerSfn);
    engineParameterAndReadyEventMakerSfn.grantStartExecution(inputMakerSfn);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'library_qc_complete_to_tn_draft', {
      ruleName: `stacky-${this.TnReadyMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.TnReadyMap.triggerSource],
        detailType: [this.TnReadyMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.TnReadyMap.triggerStatus }],
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
