import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
### Construct C (Part 1)

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `orcabus.librarystatechange`
Input Event status: `fastqlistrowregistered`

First bit:

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `awaitinginput`

Second bit:

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `orcabus.workflowrunstatechange`
Output Event status: `ready`

* The ctTSOv2InputMaker Construct
  * Subscribes to the FastqListRowEventHandler Construct outputs and creates the input for the ctTSOv2ReadySfn
  * Pushes an event payload of the input for the ctTSOv2ReadyEventSubmitters
  * From the awaiting input event, we then generate a workflow ready status for each of the cttso run workflows

*/

export interface fastqListRowsToCttsov2InputMakerConstructProps {
  tableObj: dynamodb.ITableV2;
  instrumentRunTableObj: dynamodb.ITableV2;
  icav2ProjectIdSsmParameterObj: ssm.IStringParameter;
  outputUriPrefixSsmParameterObj: ssm.IStringParameter;
  eventBusObj: events.IEventBus;
}

export class fastqListRowsToCttsov2InputMakerConstruct extends Construct {
  public readonly fastqListRowsTocttsov2InputMakerEventMap = {
    prefix: 'cttsov2InputMakerScatter',
    localTablePartition: 'fastqlistrows_to_cttsov2',
    samplesheetTablePartitionName: 'samplesheet_by_instrument_run',
    fastqListRowTablePartitionName: 'fastqlistrows_by_instrument_run',
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'fastqlistrowregistered',
    triggerDetailType: 'libraryStateChange',
    triggerWorkflowName: 'bclconvert_interop_qc',
    outputDetailType: 'workflowRunStateChange',
    outputSource: 'orcabus.cttsov2inputeventglue',
    outputStatus: 'awaitinginput',
    payloadVersion: '2024.05.24',
    workflowName: 'cttsov2',
    workflowVersion: '2.1.1',
  };

  constructor(scope: Construct, id: string, props: fastqListRowsToCttsov2InputMakerConstructProps) {
    super(scope, id);

    /*
        Part 1: Build the lambdas
        */

    // Translate the libraryrunstatechange event
    const libraryrunstatechange_lambda_obj = new PythonFunction(
      this,
      'translate_libraryrunstatechange_event_lambda',
      {
        entry: path.join(__dirname, 'lambdas', 'handle_libraryrunstatechange_py'),
        index: 'handle_libraryrunstatechange.py',
        handler: 'handler',
        runtime: Runtime.PYTHON_3_11,
        architecture: Architecture.ARM_64,
      }
    );

    // Get the library id set from the libraryrunstatechange event
    const get_library_ids_lambda_obj = new PythonFunction(this, 'get_library_ids_event_lambda', {
      entry: path.join(__dirname, 'lambdas', 'get_library_ids_py'),
      index: 'get_library_ids.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_11,
      architecture: Architecture.ARM_64,
    });

    // Collect the samplesheet slimmer
    const samplesheet_slim_lambda_obj = new PythonFunction(this, 'samplesheet_slim_lambda', {
      entry: path.join(__dirname, 'lambdas', 'slim_samplesheet_py'),
      index: 'slim_samplesheet.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_11,
      architecture: Architecture.ARM_64,
    });

    // Collect the fastq list row slimmer
    const fastq_list_row_slim_lambda_obj = new PythonFunction(this, 'fastq_list_row_slim_lambda', {
      entry: path.join(__dirname, 'lambdas', 'slim_fastq_list_rows_py'),
      index: 'slim_fastq_list_rows.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_11,
      architecture: Architecture.ARM_64,
    });

    /*
        Part 2: Build the sfn
        */
    const inputMakerScatterSfn = new sfn.StateMachine(this, 'cttsov2_inputs_generator', {
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'fastq_list_rows_registered_to_cttsov2_input_maker_event_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __local_table_name__: props.tableObj.tableName,
        __table_partition_name__: this.fastqListRowsTocttsov2InputMakerEventMap.localTablePartition,
        __instrument_run_id_table_name__: props.instrumentRunTableObj.tableName,
        __samplesheet_partition_name__:
          this.fastqListRowsTocttsov2InputMakerEventMap.samplesheetTablePartitionName,
        __fastq_list_row_partition_name__:
          this.fastqListRowsTocttsov2InputMakerEventMap.fastqListRowTablePartitionName,
        __translate_event_lambda_function_arn__:
          libraryrunstatechange_lambda_obj.currentVersion.functionArn,
        __get_library_set_lambda_function_arn__:
          get_library_ids_lambda_obj.currentVersion.functionArn,
        __slim_samplesheet_lambda_function_arn__:
          samplesheet_slim_lambda_obj.currentVersion.functionArn,
        __slim_fastq_list_row_lambda_function_arn__:
          fastq_list_row_slim_lambda_obj.currentVersion.functionArn,
        __workflow_name__: this.fastqListRowsTocttsov2InputMakerEventMap.workflowName,
        __workflow_version__: this.fastqListRowsTocttsov2InputMakerEventMap.workflowVersion,
        __detail_type__: this.fastqListRowsTocttsov2InputMakerEventMap.outputDetailType,
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.fastqListRowsTocttsov2InputMakerEventMap.outputSource,
      },
    });

    /*
        Part 2: Update the permissions
        */

    // Allow lambdas to be invoked by the step function
    [
      libraryrunstatechange_lambda_obj,
      get_library_ids_lambda_obj,
      samplesheet_slim_lambda_obj,
      fastq_list_row_slim_lambda_obj,
    ].forEach((lambda) => {
      lambda.currentVersion.grantInvoke(inputMakerScatterSfn.role);
    });

    // Allow the step function to write to the event bus
    props.eventBusObj.grantPutEventsTo(inputMakerScatterSfn.role);

    /*
        Part 3: Create rule to trigger this event
        */
    const eventRule = new events.Rule(
      this,
      'scatter_cttsov2_input_maker_jobs_on_new_fastq_list_rows',
      {
        eventBus: props.eventBusObj,
        eventPattern: {
          source: [this.fastqListRowsTocttsov2InputMakerEventMap.triggerSource],
          detailType: [this.fastqListRowsTocttsov2InputMakerEventMap.triggerDetailType],
          detail: {
            status: [this.fastqListRowsTocttsov2InputMakerEventMap.triggerStatus],
            workflowName: [this.fastqListRowsTocttsov2InputMakerEventMap.triggerWorkflowName],
          },
        },
      }
    );

    // Add target to event rule
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(inputMakerScatterSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
