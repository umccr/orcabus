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

* Initialise wgts instrument db construct

// FIXME - library construct should not overwrite the existing library, need to check if the library exists in db first
*/

export interface WgtsQcInitialiseLibraryAndFastqListRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WgtsQcInitialiseLibraryAndFastqListRowConstruct extends Construct {
  public readonly WgtsQcInitialiseLibraryAndFastqListRowMap = {
    prefix: 'wgtsQcInitialiseLibraryAndFastqListRow',
    tablePartition: {
      instrument: 'instrument_run',
      library: 'library',
      fastqListRow: 'fastq_list_row',
    },
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'LibraryInSamplesheet',
    triggerDetailType: 'SamplesheetMetadataUnion',
    triggerSampleType: {
      WGS: 'WGS',
      WTS: 'WTS',
    },
    triggerWorkflowType: {
      QC: 'qc',
      RESEARCH: 'research',
      CLINICAL: 'clinical',
    },
  };

  constructor(
    scope: Construct,
    id: string,
    props: WgtsQcInitialiseLibraryAndFastqListRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_instrument_run_db_row', {
      stateMachineName: `${this.WgtsQcInitialiseLibraryAndFastqListRowMap.prefix}-initialise-run-db-row`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'initialise_wgts_library_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* General */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __instrument_run_partition_name__:
          this.WgtsQcInitialiseLibraryAndFastqListRowMap.tablePartition.instrument,
        __library_partition_name__:
          this.WgtsQcInitialiseLibraryAndFastqListRowMap.tablePartition.library,
        __fastq_list_row_partition_name__:
          this.WgtsQcInitialiseLibraryAndFastqListRowMap.tablePartition.fastqListRow,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    /*
    Part 3: Subscribe to the library events from the event bus where the library assay type
    is WGS or WTS and the workflow is QC, RESEARCH or CLINICAL
    */
    const rule = new events.Rule(this, 'initialise_library_assay', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WgtsQcInitialiseLibraryAndFastqListRowMap.triggerSource],
        detailType: [this.WgtsQcInitialiseLibraryAndFastqListRowMap.triggerDetailType],
        detail: {
          payload: {
            data: {
              library: {
                type: [
                  {
                    'equals-ignore-case':
                      this.WgtsQcInitialiseLibraryAndFastqListRowMap.triggerSampleType.WGS,
                  },
                  {
                    'equals-ignore-case':
                      this.WgtsQcInitialiseLibraryAndFastqListRowMap.triggerSampleType.WTS,
                  },
                ],
                workflow: [
                  {
                    'equals-ignore-case':
                      this.WgtsQcInitialiseLibraryAndFastqListRowMap.triggerWorkflowType.QC,
                  },
                  {
                    'equals-ignore-case':
                      this.WgtsQcInitialiseLibraryAndFastqListRowMap.triggerWorkflowType.RESEARCH,
                  },
                  {
                    'equals-ignore-case':
                      this.WgtsQcInitialiseLibraryAndFastqListRowMap.triggerWorkflowType.CLINICAL,
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
