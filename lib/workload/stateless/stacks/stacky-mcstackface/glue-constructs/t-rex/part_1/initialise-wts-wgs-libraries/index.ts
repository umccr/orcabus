/*
Populate oncoanalyser stacky-db from wts and wgs libraries
*/

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

* Initialise oncoanalyser instrument db construct
*/

export interface OncoanalyserBothInitialiseLibraryAndFastqListRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class OncoanalyserInitialiseLibraryAndFastqListRowConstruct extends Construct {
  public readonly OncoanalyserInitialiseLibraryAndFastqListRowMap = {
    prefix: 'handypal-make-library-and-fqlr-row',
    tablePartition: {
      subject: 'subject',
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
      RESEARCH: 'research',
      CLINICAL: 'clinical',
    },
    triggerPhenotypeType: {
      NORMAL: 'normal',
      TUMOR: 'tumor',
    },
  };

  constructor(
    scope: Construct,
    id: string,
    props: OncoanalyserBothInitialiseLibraryAndFastqListRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_oncoanalyser_library_db_row', {
      stateMachineName: `${this.OncoanalyserInitialiseLibraryAndFastqListRowMap.prefix}-initialise-oncoanalyser-library-db`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'initialise_wts_and_wgs_libraries_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* General */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __subject_partition_name__:
          this.OncoanalyserInitialiseLibraryAndFastqListRowMap.tablePartition.subject,
        __library_partition_name__:
          this.OncoanalyserInitialiseLibraryAndFastqListRowMap.tablePartition.library,
        __fastq_list_row_partition_name__:
          this.OncoanalyserInitialiseLibraryAndFastqListRowMap.tablePartition.fastqListRow,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    /*
    Part 3: Subscribe to the library events from the event bus where the library assay type
    is WGS and the workflow is RESEARCH or CLINICAL
    and where the phenotype is NORMAL or TUMOR
    */
    const rule = new events.Rule(this, 'initialise_library_assay', {
      ruleName: `stacky-${this.OncoanalyserInitialiseLibraryAndFastqListRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerSource],
        detailType: [this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerDetailType],
        detail: {
          payload: {
            data: {
              library: {
                type: [
                  {
                    'equals-ignore-case':
                      this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerSampleType.WGS,
                  },
                  {
                    'equals-ignore-case':
                      this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerSampleType.WTS,
                  },
                ],
                workflow: [
                  {
                    'equals-ignore-case':
                      this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerWorkflowType
                        .RESEARCH,
                  },
                  {
                    'equals-ignore-case':
                      this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerWorkflowType
                        .CLINICAL,
                  },
                ],
                phenotype: [
                  {
                    'equals-ignore-case':
                      this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerPhenotypeType
                        .NORMAL,
                  },
                  {
                    'equals-ignore-case':
                      this.OncoanalyserInitialiseLibraryAndFastqListRowMap.triggerPhenotypeType
                        .TUMOR,
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
