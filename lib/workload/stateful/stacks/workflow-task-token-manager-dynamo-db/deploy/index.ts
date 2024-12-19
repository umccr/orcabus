import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface WorkflowTaskTokenTableConfig {
  dynamodbTableName: string;
}

export type WorkflowTaskTokenTableStackProps = WorkflowTaskTokenTableConfig & cdk.StackProps;

export class WorkflowTaskTokenTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props: WorkflowTaskTokenTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table with id and sort keys
    */
    new DynamodbPartitionedPipelineConstruct(this, props.dynamodbTableName, {
      tableName: props.dynamodbTableName,
    });
  }
}
