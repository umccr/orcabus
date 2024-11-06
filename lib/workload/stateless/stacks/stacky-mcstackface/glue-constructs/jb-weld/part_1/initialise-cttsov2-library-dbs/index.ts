import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 2

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `SamplesheetMetadataUnion`
Input Event status: `LibraryInSamplesheet`

* Initialise cttsov2 instrument db construct
*/

export interface Cttsov2InitialiseLibraryAndFastqListRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class Cttsov2InitialiseLibraryAndFastqListRowConstruct extends Construct {
  public readonly Cttsov2InitialiseLibraryAndFastqListRowMap = {
    prefix: 'jbweld-make-library-and-fqlr-row',
    tablePartition: {
      instrument: 'instrument_run',
      library: 'library',
      bclconvertDataRow: 'bclconvert_data',
      fastqListRow: 'fastq_list_row',
    },
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'LibraryInSamplesheet',
    triggerDetailType: 'SamplesheetMetadataUnion',
    triggerAssayType: {
      v1: 'cttso',
      v2: 'cttsov2',
    },
    ntc_prefix: 'NTC',
  };

  constructor(
    scope: Construct,
    id: string,
    props: Cttsov2InitialiseLibraryAndFastqListRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_instrument_run_db_row', {
      stateMachineName: `${this.Cttsov2InitialiseLibraryAndFastqListRowMap.prefix}-initialise-run-db-row`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'initialise_cttsov2_library_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* General */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __instrument_run_partition_name__:
          this.Cttsov2InitialiseLibraryAndFastqListRowMap.tablePartition.instrument,
        __library_partition_name__:
          this.Cttsov2InitialiseLibraryAndFastqListRowMap.tablePartition.library,
        __fastq_list_row_partition_name__:
          this.Cttsov2InitialiseLibraryAndFastqListRowMap.tablePartition.fastqListRow,
        __bclconvert_data_row_partition_name__:
          this.Cttsov2InitialiseLibraryAndFastqListRowMap.tablePartition.bclconvertDataRow,
      },
    });

    /*
    Part 3: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    /*
    Part 4: Subscribe to the library events from the event bus where the library assay type is cttsov2
    */
    const rule = new events.Rule(this, 'initialise_library_assay', {
      ruleName: `stacky-${this.Cttsov2InitialiseLibraryAndFastqListRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.Cttsov2InitialiseLibraryAndFastqListRowMap.triggerSource],
        detailType: [this.Cttsov2InitialiseLibraryAndFastqListRowMap.triggerDetailType],
        detail: {
          payload: {
            data: {
              library: {
                assay: [
                  {
                    'equals-ignore-case':
                      this.Cttsov2InitialiseLibraryAndFastqListRowMap.triggerAssayType.v1,
                  },
                  {
                    'equals-ignore-case':
                      this.Cttsov2InitialiseLibraryAndFastqListRowMap.triggerAssayType.v2,
                  },
                ],
              },
              // Dont add the ntc to the list of libraries to process
              sample: {
                sampleId: [
                  {
                    'anything-but': {
                      prefix: this.Cttsov2InitialiseLibraryAndFastqListRowMap.ntc_prefix,
                    },
                  },
                ],
              },
            },
          },
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
