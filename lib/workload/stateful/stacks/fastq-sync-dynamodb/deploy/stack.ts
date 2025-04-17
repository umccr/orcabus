import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface FastqSyncTableConfig {
  dynamodbTableName: string;
}

export type FastqSyncManagerTableStackProps = FastqSyncTableConfig & cdk.StackProps;

export class FastqSyncManagerTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props: FastqSyncManagerTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where id_type is the primary sort key
    */
    new DynamodbPartitionedPipelineConstruct(this, 'fastq_sync_table', {
      tableName: props.dynamodbTableName,
    });
  }
}
