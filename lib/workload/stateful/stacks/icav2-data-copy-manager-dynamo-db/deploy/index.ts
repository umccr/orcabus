import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface Icav2DataCopyManagerTableConfig {
  dynamodbTableName: string;
}

export type Icav2DataCopyManagerTableStackProps = Icav2DataCopyManagerTableConfig & cdk.StackProps;

export class Icav2DataCopyManagerTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props: Icav2DataCopyManagerTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table with id and sort keys
    */
    new DynamodbPartitionedPipelineConstruct(this, props.dynamodbTableName, {
      tableName: props.dynamodbTableName,
    });
  }
}
