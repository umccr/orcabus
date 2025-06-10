import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 2

Input Event Source: `orcabus.fastqglue`
Input Event DetailType: `SamplesheetMetadataUnion`
Input Event status: `LibraryInSamplesheet`

* Initialise rnasum instrument db construct
*/

export interface RnasumInitialiseLibraryConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class RnasumInitialiseLibraryConstruct extends Construct {
  public readonly RnasumInitialiseLibraryAndFastqListRowMap = {
    prefix: 'roket-make-library',
    tablePartition: {
      library: 'library',
    },
    triggerSource: 'orcabus.fastqglue',
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
      TUMOR: 'tumor',
    },
  };

  constructor(scope: Construct, id: string, props: RnasumInitialiseLibraryConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_rnasum_library_db_row', {
      stateMachineName: `${this.RnasumInitialiseLibraryAndFastqListRowMap.prefix}-initialise-rnasum-library-db`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_functions_templates', 'initialise_library_db_template.asl.json')
      ),
      definitionSubstitutions: {
        /* General */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __library_partition_name__:
          this.RnasumInitialiseLibraryAndFastqListRowMap.tablePartition.library,
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
      ruleName: `stacky-${this.RnasumInitialiseLibraryAndFastqListRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.RnasumInitialiseLibraryAndFastqListRowMap.triggerSource],
        detailType: [this.RnasumInitialiseLibraryAndFastqListRowMap.triggerDetailType],
        detail: {
          payload: {
            data: {
              library: {
                type: [
                  {
                    'equals-ignore-case':
                      this.RnasumInitialiseLibraryAndFastqListRowMap.triggerSampleType.WGS,
                  },
                  {
                    'equals-ignore-case':
                      this.RnasumInitialiseLibraryAndFastqListRowMap.triggerSampleType.WTS,
                  },
                ],
                workflow: [
                  {
                    'equals-ignore-case':
                      this.RnasumInitialiseLibraryAndFastqListRowMap.triggerWorkflowType.RESEARCH,
                  },
                  {
                    'equals-ignore-case':
                      this.RnasumInitialiseLibraryAndFastqListRowMap.triggerWorkflowType.CLINICAL,
                  },
                ],
                phenotype: [
                  {
                    'equals-ignore-case':
                      this.RnasumInitialiseLibraryAndFastqListRowMap.triggerPhenotypeType.TUMOR,
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
