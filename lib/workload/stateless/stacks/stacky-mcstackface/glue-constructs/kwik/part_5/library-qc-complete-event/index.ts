import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';

/*
Part 7

Input Event Source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: `FastqListRowStateChange`
Input Event status: `QcComplete`

Output Event Source: `orcabus.wgtsqcinputeventglue`
Output Event DetailType: `LibraryStateChange`
Output Event status: `QcComplete`

* Once all fastq list rows have been processed for a given library, we fire off a library state change event
* This will contain the qc information such as coverage + duplicate rate (for wgs) or exon coverage (for wts)

*/

export interface WgtsQcLibraryQcCompleteConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WgtsQcLibraryQcCompleteConstruct extends Construct {
  public readonly WgtsQcLibraryQcCompleteMap = {
    prefix: 'kwik-library-qc-complete',
    tablePartitions: {
      library: 'library',
      fastq_list_row: 'fastq_list_row',
    },
    payloadVersion: '2024.07.16',
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'QC_COMPLETE',
    triggerDetailType: 'FastqListRowStateChange',
    outputSource: 'orcabus.wgtsqcinputeventglue',
    outputDetailType: 'LibraryStateChange',
    outputStatus: 'QC_COMPLETE',
  };

  constructor(scope: Construct, id: string, props: WgtsQcLibraryQcCompleteConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */

    const sumCoveragesLambdaObj = new PythonFunction(this, 'sum_coverages_for_rgids_py', {
      entry: path.join(__dirname, 'lambdas', 'sum_coverages_for_rgids_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'sum_coverages_for_rgids.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 1: Build the sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_instrument_run_db_row', {
      stateMachineName: `${this.WgtsQcLibraryQcCompleteMap.prefix}-initialise-run-db-row`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'wgts_library_qc_complete_event_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Event stuff */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.WgtsQcLibraryQcCompleteMap.outputSource,
        __detail_type__: this.WgtsQcLibraryQcCompleteMap.outputDetailType,
        __payload_version__: this.WgtsQcLibraryQcCompleteMap.payloadVersion,
        __status__: this.WgtsQcLibraryQcCompleteMap.outputStatus,
        /* Table stuff */
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_partition__:
          this.WgtsQcLibraryQcCompleteMap.tablePartitions.fastq_list_row,
        __library_partition__: this.WgtsQcLibraryQcCompleteMap.tablePartitions.library,
        /* Lambdas */
        __sum_coverages_for_rgids_lambda_function_arn__:
          sumCoveragesLambdaObj.currentVersion.functionArn,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);
    // invoke the lambda function
    sumCoveragesLambdaObj.currentVersion.grantInvoke(inputMakerSfn.role);
    // Push events to the event bus
    props.eventBusObj.grantPutEventsTo(inputMakerSfn.role);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'wgts_subscribe_to_fastq_list_row_qc_complete', {
      ruleName: `stacky-${this.WgtsQcLibraryQcCompleteMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WgtsQcLibraryQcCompleteMap.triggerSource],
        detailType: [this.WgtsQcLibraryQcCompleteMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.WgtsQcLibraryQcCompleteMap.triggerStatus }],
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
