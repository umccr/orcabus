import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface PierianDxPipelineTableConfig {
  dynamodbTableName: string;
}

export type PierianDxPipelineTableStackProps = PierianDxPipelineTableConfig & cdk.StackProps;

export class PierianDxPipelineTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props: PierianDxPipelineTableStackProps) {
    super(scope, id, props);

    /*
        Initialise dynamodb table, where portal_run_id is the primary sort key
        */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'pieriandx_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );
  }
}
