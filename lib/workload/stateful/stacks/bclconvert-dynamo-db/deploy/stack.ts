import { Stack, RemovalPolicy, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DynamodbIcav2PipelineConstruct } from '../../../../components/dynamodb-icav2-table';

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
    return new DynamodbIcav2PipelineConstruct(this, 'icav2_event_translator_table', {
      tableName: props.dynamodbTableName,
      removalPolicy: props.removalPolicy,
    });
  }
}
