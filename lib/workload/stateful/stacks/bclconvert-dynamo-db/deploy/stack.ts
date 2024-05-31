import { Stack, RemovalPolicy, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {DynamodbPartitionedPipelineConstruct} from "../../../../components/dynamodb-partitioned-table";

export interface BclConvertTableStackProps {
  dynamodbTableName: string;
  removalPolicy?: RemovalPolicy;
}

export class BclConvertTable extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & BclConvertTableStackProps) {
    super(scope, id, props);
    this.createICAv2EventTranslatorTable(props);
  }

  private createICAv2EventTranslatorTable(props: BclConvertTableStackProps) {
    return new DynamodbPartitionedPipelineConstruct(this, 'icav2_event_translator_table', {
      tableName: props.dynamodbTableName,
      removalPolicy: props.removalPolicy,
    });
  }
}
