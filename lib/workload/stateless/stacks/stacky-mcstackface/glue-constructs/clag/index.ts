import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { NewSamplesheetEventShowerConstruct } from './part_1/samplesheet-event-shower';
import { NewFastqListRowsEventShowerConstruct } from './part_2/fastq-list-rows-event-shower';

/*
Provide the glue to push 'shower' events
When either new fastq list rows arrive or when a new samplesheet arrives
*/

export interface showerGlueHandlerConstructProps {
  eventBusObj: events.IEventBus;
  instrumentRunTableObj: dynamodb.ITableV2;
}

export class showerGlueHandlerConstruct extends Construct {
  constructor(scope: Construct, id: string, props: showerGlueHandlerConstructProps) {
    super(scope, id);

    /*
    Part 1
    */
    const sampleSheetShowerConstruct = new NewSamplesheetEventShowerConstruct(
      this,
      'samplesheet_shower',
      {
        // Event bus
        eventBusObj: props.eventBusObj,
        // Tables
        tableObj: props.instrumentRunTableObj,
      }
    );

    /*
    Part 2
    */
    const fastqListRowShower = new NewFastqListRowsEventShowerConstruct(
      this,
      'fastq_list_rows_shower',
      {
        // Event bus
        eventBusObj: props.eventBusObj,
        // Tables
        tableObj: props.instrumentRunTableObj,
      }
    );
  }
}
