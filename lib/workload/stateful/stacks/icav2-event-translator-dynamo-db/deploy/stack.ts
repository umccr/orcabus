import { Stack, RemovalPolicy, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import {DynamodbPartitionedPipelineConstruct} from "../../../../components/dynamodb-partitioned-table";

export interface Icav2EventTranslatorTableStackProps {
  dynamodbTableName: string;
  removalPolicy?: RemovalPolicy;
}

export class Icav2EventTranslatorTable extends Stack {
  readonly icav2EventTranslatorDynamodbTable: dynamodb.Table;
  constructor(
    scope: Construct,
    id: string,
    props: StackProps & Icav2EventTranslatorTableStackProps
  ) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    new DynamodbPartitionedPipelineConstruct(this, 'icav2_event_translator_table', {
      tableName: props.dynamodbTableName,
      removalPolicy: props.removalPolicy,
    });
  }
}
