import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 1

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `SamplesheetMetadataUnion`
Input Event status: `SubjectInSamplesheet`

* Initialise rnasum subject db construct
*/

export interface RnasumInitialiseSubjectDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class RnasumInitialiseSubjectDbRowConstruct extends Construct {
  public readonly RnasumInitialiseSubjectDbRowMap = {
    prefix: 'roket-make-subject-row',
    tablePartition: 'subject',
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'SubjectInSamplesheet',
    triggerDetailType: 'SamplesheetMetadataUnion',
  };

  constructor(scope: Construct, id: string, props: RnasumInitialiseSubjectDbRowConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_subject_db_row', {
      stateMachineName: `${this.RnasumInitialiseSubjectDbRowMap.prefix}-initialise-subject`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'initialise_rnasum_subject_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __subject_partition_name__: this.RnasumInitialiseSubjectDbRowMap.tablePartition,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'rnasum_subscribe_to_samplesheet_shower_subject', {
      ruleName: `stacky-${this.RnasumInitialiseSubjectDbRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.RnasumInitialiseSubjectDbRowMap.triggerSource],
        detailType: [this.RnasumInitialiseSubjectDbRowMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.RnasumInitialiseSubjectDbRowMap.triggerStatus }],
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
