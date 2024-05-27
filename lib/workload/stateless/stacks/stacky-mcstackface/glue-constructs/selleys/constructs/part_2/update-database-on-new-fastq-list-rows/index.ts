import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import path from 'path';
import { LambdaB64GzTranslatorConstruct } from '../../../../../../../../components/lambda-b64gz-translator';

export interface updateDataBaseOnNewFastqListRowsEventConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class updateDataBaseOnNewFastqListRowsEventConstruct extends Construct {
  public declare updateDataBaseOnNewFastqListRowsEventMap: {
    prefix: 'updateDatabaseOnNewFastqListRows';
    tablePartition: 'fastqlistrows_by_instrument_run';
    triggerSource: 'orcabus.workflowmanager';
    triggerStatus: 'succeeded';
    triggerDetailType: 'workflowRunStateChange';
    triggerWorkflowName: 'bssh_fastq_copy';
    outputSource: 'orcabus.instrumentrunmanager';
    outputStatus: 'fastqlistrowsregistered';
    outputDetailType: 'instrumentRunStateChange';
  };

  public readonly stateMachineObj: sfn.StateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: updateDataBaseOnNewFastqListRowsEventConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build decompression lambda
    */
    const decompressFastqListRowLambda = new LambdaB64GzTranslatorConstruct(
      this,
      'lambda_b64gz_translator_lambda',
      {
        functionNamePrefix: this.updateDataBaseOnNewFastqListRowsEventMap.prefix,
      }
    ).lambdaObj;

    /*
    Part 2: Build state machine
    */
    this.stateMachineObj = new sfn.StateMachine(this, 'update_database_on_new_fastq_list_row_sfn', {
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'update_database_on_new_samplesheet.asl.simple.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __table_partition_name__: this.updateDataBaseOnNewFastqListRowsEventMap.tablePartition,
        __detail_type__: this.updateDataBaseOnNewFastqListRowsEventMap.outputDetailType,
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.updateDataBaseOnNewFastqListRowsEventMap.outputSource,
        __decompress_fastq_list_rows_lambda_function_arn__:
          decompressFastqListRowLambda.currentVersion.functionArn,
      },
    });

    /*
    Part 3: Wire up permissions
    */
    /* Allow state machine to write to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    /* Allow state machine to invoke lambda */
    decompressFastqListRowLambda.currentVersion.grantInvoke(this.stateMachineObj.role);

    /* Allow state machine to send events */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);

    /*
    Part 4: Build event rule
    */
    const eventRule = new events.Rule(this, 'update_database_on_new_samplesheet_event_rule', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.updateDataBaseOnNewFastqListRowsEventMap.triggerSource],
        detailType: [this.updateDataBaseOnNewFastqListRowsEventMap.triggerDetailType],
        detail: {
          status: [this.updateDataBaseOnNewFastqListRowsEventMap.triggerStatus],
          workflowName: [this.updateDataBaseOnNewFastqListRowsEventMap.triggerWorkflowName],
        },
      },
    });

    eventRule.addTarget(new eventsTargets.SfnStateMachine(this.stateMachineObj));
    eventRule.addTarget(
        new eventsTargets.SfnStateMachine(this.stateMachineObj, {
            input: events.RuleTargetInput.fromEventPath('$.detail'),
        })
    );
  }
}
