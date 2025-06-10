import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 1

Input Event Source: `orcabus.fastqglue`
Input Event DetailType: `SamplesheetMetadataUnion`
Input Event status: `LibraryInSamplesheet`

* Initialise wts instrument db construct
*/

export interface WtsInitialiseLibraryAndFastqListRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WtsInitialiseLibraryAndFastqListRowConstruct extends Construct {
  public readonly WtsInitialiseLibraryAndFastqListRowMap = {
    prefix: 'modpodge-wts-make-library-row',
    tablePartition: {
      library: 'library',
      fastqListRow: 'fastq_list_row',
    },
    triggerSource: 'orcabus.fastqglue',
    triggerStatus: 'LibraryInSamplesheet',
    triggerDetailType: 'SamplesheetMetadataUnion',
    triggerSampleType: {
      WTS: 'WTS',
    },
    triggerWorkflowType: {
      RESEARCH: 'research',
      CLINICAL: 'clinical',
    },
    triggerPhenotypeType: {
      TUMOR: 'tumor',
    },
  };

  constructor(
    scope: Construct,
    id: string,
    props: WtsInitialiseLibraryAndFastqListRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_wts_library_db_row', {
      stateMachineName: `${this.WtsInitialiseLibraryAndFastqListRowMap.prefix}-initialise-wts-library-db`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'initialise_wts_library_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* General */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __library_partition_name__:
          this.WtsInitialiseLibraryAndFastqListRowMap.tablePartition.library,
        __fastq_list_row_partition_name__:
          this.WtsInitialiseLibraryAndFastqListRowMap.tablePartition.fastqListRow,
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
      ruleName: `stacky-${this.WtsInitialiseLibraryAndFastqListRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WtsInitialiseLibraryAndFastqListRowMap.triggerSource],
        detailType: [this.WtsInitialiseLibraryAndFastqListRowMap.triggerDetailType],
        detail: {
          payload: {
            data: {
              library: {
                type: [
                  {
                    'equals-ignore-case':
                      this.WtsInitialiseLibraryAndFastqListRowMap.triggerSampleType.WTS,
                  },
                ],
                workflow: [
                  {
                    'equals-ignore-case':
                      this.WtsInitialiseLibraryAndFastqListRowMap.triggerWorkflowType.RESEARCH,
                  },
                  {
                    'equals-ignore-case':
                      this.WtsInitialiseLibraryAndFastqListRowMap.triggerWorkflowType.CLINICAL,
                  },
                ],
                phenotype: [
                  {
                    'equals-ignore-case':
                      this.WtsInitialiseLibraryAndFastqListRowMap.triggerPhenotypeType.TUMOR,
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
