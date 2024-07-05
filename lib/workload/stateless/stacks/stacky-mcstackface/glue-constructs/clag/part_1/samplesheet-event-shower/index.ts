import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import path from 'path';
import { LambdaB64GzTranslatorConstruct } from '../../../../../../../components/python-lambda-b64gz-translator';
import { GetLibraryObjectsFromSamplesheetConstruct } from '../../../../../../../components/python-lambda-get-metadata-objects-from-samplesheet';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';

export interface NewSamplesheetEventShowerConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class NewSamplesheetEventShowerConstruct extends Construct {
  public readonly newSamplesheetEventShowerMap = {
    // General
    prefix: 'newSamplesheetEventShower',
    // Tables
    tablePartition: {
      samplesheetByInstrumentRun: 'samplesheet_by_instrument_run',
      subject: 'subject',
      library: 'library',
    },
    // Set event triggers
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bclconvert',
    // Set event outputs
    outputSource: 'orcabus.instrumentrunmanager',
    outputStatus: {
      startEventShower: 'SamplesheetRegisteredEventShowerStarting',
      completeEventShower: 'SamplesheetRegisteredEventShowerComplete',
      subjectInSamplesheet: 'SubjectInSamplesheet',
      libraryInSamplesheet: 'LibraryInSamplesheet',
    },
    outputDetailType: {
      showerTerminal: 'SamplesheetShowerStateChange',
      metadataInSampleSheet: 'SamplesheetMetadataUnion',
    },
    outputPayloadVersion: '0.1.0',
  };

  public readonly stateMachineObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: NewSamplesheetEventShowerConstructProps) {
    super(scope, id);

    /*
        Part 1: Build lambdas
        */

    // Decompression lambda
    const decompressSamplesheetLambda = new LambdaB64GzTranslatorConstruct(
      this,
      'lambda_b64gz_translator_lambda',
      {
        functionNamePrefix: this.newSamplesheetEventShowerMap.prefix,
      }
    ).lambdaObj;

    // Get Library / Subject Map from Samplesheet
    const getLibrarySubjectMapLambda = new GetLibraryObjectsFromSamplesheetConstruct(
      this,
      'get_library_subject_map_lambda',
      {
        functionNamePrefix: this.newSamplesheetEventShowerMap.prefix,
      }
    ).lambdaObj;

    // Generate Data Objects from SampleSheet lambda (local lambda)
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
      }
    );

    /*
        Part 2: Build state machine
        */
    this.stateMachineObj = new sfn.StateMachine(this, 'update_database_on_new_samplesheet_sfn', {
      stateMachineName: `${this.newSamplesheetEventShowerMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'samplesheet_event_shower_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Standard event settings */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.newSamplesheetEventShowerMap.outputSource,

        /* Specific Event settings */
        // Start Event Shower
        __start_samplesheet_shower_detail_type__:
          this.newSamplesheetEventShowerMap.outputDetailType.showerTerminal,
        __start_samplesheet_shower_payload_version__:
          this.newSamplesheetEventShowerMap.outputPayloadVersion,
        __start_samplesheet_shower_status__:
          this.newSamplesheetEventShowerMap.outputStatus.startEventShower,

        // Subject In Samplesheet
        __subject_in_samplesheet_detail_type__:
          this.newSamplesheetEventShowerMap.outputDetailType.metadataInSampleSheet,
        __subject_in_samplesheet_payload_version__:
          this.newSamplesheetEventShowerMap.outputPayloadVersion,
        __subject_in_samplesheet_status__:
          this.newSamplesheetEventShowerMap.outputStatus.subjectInSamplesheet,

        // Library In Samplesheet
        __library_in_samplesheet_detail_type__:
          this.newSamplesheetEventShowerMap.outputDetailType.metadataInSampleSheet,
        __library_in_samplesheet_payload_version__:
          this.newSamplesheetEventShowerMap.outputPayloadVersion,
        __library_in_samplesheet_status__:
          this.newSamplesheetEventShowerMap.outputStatus.libraryInSamplesheet,

        // Complete Event Shower
        __complete_samplesheet_shower_detail_type__:
          this.newSamplesheetEventShowerMap.outputDetailType.showerTerminal,
        __complete_samplesheet_shower_payload_version__:
          this.newSamplesheetEventShowerMap.outputPayloadVersion,
        __complete_samplesheet_shower_status__:
          this.newSamplesheetEventShowerMap.outputStatus.completeEventShower,

        /* Table settings */
        __table_name__: props.tableObj.tableName,
        __subject_table_partition_name__: this.newSamplesheetEventShowerMap.tablePartition.subject,
        __library_table_partition_name__: this.newSamplesheetEventShowerMap.tablePartition.library,
        __samplesheet_table_partition_name__:
          this.newSamplesheetEventShowerMap.tablePartition.samplesheetByInstrumentRun,

        // Lambdas
        __decompress_samplesheet_function_arn__:
          decompressSamplesheetLambda.currentVersion.functionArn,
        __get_subject_library_map_from_samplesheet_lambda_function_arn__:
          getLibrarySubjectMapLambda.currentVersion.functionArn,
        __generate_event_objects_lambda_function_arn__:
          generateEventDataObjsLambda.currentVersion.functionArn,
      },
    });

    /*
        Part 3: Wire up permissions
        */

    /* Allow state machine to write to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    /* Allow state machine to invoke lambda */
    [decompressSamplesheetLambda, getLibrarySubjectMapLambda, generateEventDataObjsLambda].forEach(
      (lambda) => {
        lambda.currentVersion.grantInvoke(this.stateMachineObj.role);
      }
    );

    /* Allow state machine to send events */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);

    /*
        Part 4: Build event rule
        */
    const eventRule = new events.Rule(this, 'update_database_on_new_samplesheet_event_rule', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.newSamplesheetEventShowerMap.triggerSource],
        detailType: [this.newSamplesheetEventShowerMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.newSamplesheetEventShowerMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.newSamplesheetEventShowerMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target to event rule
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
