/*

Generate a suite of events for the new fastq list rows in the database

Hit the metadata manager to find the library ids, subject ids affected by the new fastq list rows

Launch an event for every subject, library and library run for the new fastq list rows

*/

import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import path from 'path';
import { LambdaB64GzTranslatorConstruct } from '../../../../../../../components/python-lambda-b64gz-translator';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import {
  Architecture,
  DockerImageCode,
  DockerImageFunction,
  Runtime,
} from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';

export interface NewFastqListRowsEventShowerConstructProps {
  /* Event Bus */
  eventBusObj: events.IEventBus;

  /* Tables */
  tableObj: dynamodb.ITableV2;

  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class NewFastqListRowsEventShowerConstruct extends Construct {
  public readonly newFastqListRowsEventShowerMap = {
    // General
    prefix: 'clag-new-fqlr-event-shower',
    // Tables
    tablePartition: {
      fastqListRowsByInstrumentRun: 'fastqlistrows_by_instrument_run',
      instrumentRun: 'instrument_run',
      subject: 'subject',
      library: 'library',
      project: 'project',
      projectEvent: 'project_event',
      fastqListRow: 'fastq_list_row',
      fastqListRowEvent: 'fastq_list_row_event',
    },
    // Set Event Triggers
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bsshFastqCopy',
    // Set Event Outputs
    outputSource: 'orcabus.instrumentrunmanager',
    outputStatus: {
      startEventShower: 'FastqListRowEventShowerStarting',
      completeEventShower: 'FastqListRowEventShowerComplete',
      newFastqListRow: 'newFastqListRow',
      newProjectPrimaryData: 'newProjectPrimaryData',
    },
    outputDetailType: {
      showerTerminal: 'FastqListRowShowerStateChange',
      fastqListRowStateChange: 'FastqListRowStateChange',
      projectDataAvailable: 'ProjectDataAvailable',
    },
    outputPayloadVersion: '0.1.0',
  };

  public readonly stateMachineObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: NewFastqListRowsEventShowerConstructProps) {
    super(scope, id);
    /*
    Part 1: Build the lambdas
    */
    // The decompression fastq list row lambda
    const decompressFastqListRowLambda = new LambdaB64GzTranslatorConstruct(
      this,
      'lambda_b64gz_translator_lambda',
      {
        functionNamePrefix: this.newFastqListRowsEventShowerMap.prefix,
      }
    ).lambdaObj;

    const cleanupFastqListRowLambda = new PythonFunction(this, 'cleanup_fastq_list_rows_lambda', {
      entry: path.join(__dirname, 'lambdas', 'clean_up_fastq_list_rows_py'),
      index: 'clean_up_fastq_list_rows.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_12,
      architecture: Architecture.ARM_64,
    });

    // Generate Data Objects
    // Translate the libraryrunstatechange event
    const generateEventDataObjsLambda = new PythonFunction(
      this,
      'generate_event_data_objects_lambda',
      {
        entry: path.join(__dirname, 'lambdas', 'generate_event_data_objects_py'),
        index: 'generate_event_data_objects.py',
        handler: 'handler',
        runtime: Runtime.PYTHON_3_12,
        architecture: Architecture.ARM_64,
        timeout: Duration.seconds(300),
        environment: {
          INSTRUMENT_RUN_TABLE_NAME: props.tableObj.tableName,
          FASTQ_LIST_ROW_EVENT_OBJ_TABLE_PARTITION_NAME:
            this.newFastqListRowsEventShowerMap.tablePartition.fastqListRowEvent,
        },
      }
    );

    // Add the demux stats
    const generateDemuxStatsLambda = new PythonFunction(this, 'generate_demux_stats_py', {
      entry: path.join(__dirname, 'lambdas', 'get_demultiplex_stats_py'),
      index: 'get_demultiplex_stats.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_12,
      architecture: Architecture.ARM_64,
      memorySize: 1024, // Don't want pandas to kill the lambda
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
      },
      timeout: Duration.seconds(300),
    });

    // Give fastqc stats lambda permission to access the secret
    props.icav2AccessTokenSecretObj.grantRead(generateDemuxStatsLambda.currentVersion);

    // Get the fastqc stats
    const architecture = lambda.Architecture.ARM_64;
    const getFastqcStats = new DockerImageFunction(this, 'get_fastqc_stats', {
      description: 'Get Fastqc stats from first 1 million reads',
      code: DockerImageCode.fromImageAsset(path.join(__dirname, 'lambdas/get_fastqc_stats'), {
        file: 'Dockerfile',
        buildArgs: {
          platform: architecture.dockerPlatform,
        },
      }),
      // Pulling data from icav2 can take time
      timeout: Duration.seconds(180), // Maximum length of lambda duration is 15 minutes
      retryAttempts: 0, // Never perform a retry if it fails
      memorySize: 2048, // Don't want pandas to kill the lambda
      architecture: architecture,
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
      },
    });

    // Give fastqc stats lambda permission to access the secret
    props.icav2AccessTokenSecretObj.grantRead(getFastqcStats.currentVersion);

    // Get the sequali stats
    const getSequaliStatsLambdaObj = new DockerImageFunction(this, 'get_sequali_stats', {
      description: 'Get the sequali stats from first 1 million reads',
      code: DockerImageCode.fromImageAsset(path.join(__dirname, 'lambdas/get_sequali_stats'), {
        file: 'Dockerfile',
        buildArgs: {
          platform: architecture.dockerPlatform,
        },
      }),
      memorySize: 2048, // Don't want pandas to kill the lambda
      timeout: Duration.seconds(300),
      architecture: Architecture.ARM_64,
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
      },
    });

    // Give the lambda permission to access the secret
    props.icav2AccessTokenSecretObj.grantRead(getSequaliStatsLambdaObj.currentVersion);

    /*
    Part 2: Build state machine
    */

    this.stateMachineObj = new sfn.StateMachine(this, 'update_database_on_new_fastq_list_row_sfn', {
      stateMachineName: `${this.newFastqListRowsEventShowerMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'fastq_list_row_event_shower_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Generate Event Configurations */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.newFastqListRowsEventShowerMap.outputSource,

        /* Specific event settings */
        // Event Shower Starting
        __fastq_list_row_transfer_starting_detail_type__:
          this.newFastqListRowsEventShowerMap.outputDetailType.showerTerminal,
        __fastq_list_row_transfer_starting_payload_version__:
          this.newFastqListRowsEventShowerMap.outputPayloadVersion,
        __fastq_list_row_transfer_starting_status__:
          this.newFastqListRowsEventShowerMap.outputStatus.startEventShower,

        // Project Data Available event
        __project_data_available_detail_type__:
          this.newFastqListRowsEventShowerMap.outputDetailType.projectDataAvailable,
        __project_data_payload_version__: this.newFastqListRowsEventShowerMap.outputPayloadVersion,
        __project_data_available_status__:
          this.newFastqListRowsEventShowerMap.outputStatus.newProjectPrimaryData,

        // New Fastq List Row
        __fastq_pair_added_detail_type__:
          this.newFastqListRowsEventShowerMap.outputDetailType.fastqListRowStateChange,
        __fastq_pair_added_payload_version__:
          this.newFastqListRowsEventShowerMap.outputPayloadVersion,
        __fastq_pair_added_status__:
          this.newFastqListRowsEventShowerMap.outputStatus.newFastqListRow,

        // Event Shower Complete
        __fastq_list_row_transfer_complete_detail_type__:
          this.newFastqListRowsEventShowerMap.outputDetailType.showerTerminal,
        __fastq_list_row_transfer_complete_payload_version__:
          this.newFastqListRowsEventShowerMap.outputPayloadVersion,
        __fastq_list_row_transfer_complete_status__:
          this.newFastqListRowsEventShowerMap.outputStatus.completeEventShower,

        /* Table settings */
        __table_name__: props.tableObj.tableName,
        __fastq_list_rows_table_partition_name__:
          this.newFastqListRowsEventShowerMap.tablePartition.fastqListRowsByInstrumentRun,
        __library_table_partition_name__:
          this.newFastqListRowsEventShowerMap.tablePartition.library,
        __instrument_run_table_partition_name__:
          this.newFastqListRowsEventShowerMap.tablePartition.instrumentRun,
        __project_table_partition_name__:
          this.newFastqListRowsEventShowerMap.tablePartition.project,
        __fastq_list_row_table_partition_name__:
          this.newFastqListRowsEventShowerMap.tablePartition.fastqListRow,
        __project_event_table_partition_name__:
          this.newFastqListRowsEventShowerMap.tablePartition.projectEvent,
        __fastq_list_row_event_table_partition_name__:
          this.newFastqListRowsEventShowerMap.tablePartition.fastqListRowEvent,

        /* Lambda functions */
        __decompress_fastq_list_rows_lambda_function_arn__:
          decompressFastqListRowLambda.currentVersion.functionArn,
        __clean_up_fastq_list_rows_lambda_function_arn__:
          cleanupFastqListRowLambda.currentVersion.functionArn,
        __generate_event_maps_lambda_function_arn__:
          generateEventDataObjsLambda.currentVersion.functionArn,
        __get_read_counts_per_rgid_lambda_function_arn__:
          generateDemuxStatsLambda.currentVersion.functionArn,
        __get_fastqc_stats_lambda_function_arn__: getFastqcStats.currentVersion.functionArn,
        __get_sequali_stats_lambda_function_arn__:
          getSequaliStatsLambdaObj.currentVersion.functionArn,
      },
    });

    /*
    Part 3: Wire up permissions
    */
    /* Allow state machine to write to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    /* Allow state machine to invoke lambda */
    [
      decompressFastqListRowLambda,
      generateEventDataObjsLambda,
      generateDemuxStatsLambda,
      getFastqcStats,
      getSequaliStatsLambdaObj,
      cleanupFastqListRowLambda,
    ].forEach((lambda) => {
      lambda.currentVersion.grantInvoke(this.stateMachineObj.role);
    });

    /* Allow 'Generate Event data objs' lambda to write to the dynamodb database */
    props.tableObj.grantReadWriteData(generateEventDataObjsLambda.currentVersion);

    /* Allow state machine to send events */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);

    /*
    Part 4: Build event rule
    */
    const eventRule = new events.Rule(this, 'update_database_on_new_fastqlistrows_event_rule', {
      ruleName: `stacky-${this.newFastqListRowsEventShowerMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.newFastqListRowsEventShowerMap.triggerSource],
        detailType: [this.newFastqListRowsEventShowerMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.newFastqListRowsEventShowerMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.newFastqListRowsEventShowerMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
