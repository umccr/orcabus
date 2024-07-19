import { Stack, RemovalPolicy, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DynamodbPartitionedPipelineConstruct } from '../../../components/dynamodb-partitioned-table';
import * as cdk from 'aws-cdk-lib';

export interface StackyStatefulTablesConfig {
  dynamodbInstrumentRunManagerTableName: string;
  dynamodbWorkflowManagerTableName: string;
  dynamodbInputGlueTableName: string;
  dynamodbCttsov2WorkflowGlueTableName: string;
  dynamodbWgtsQcGlueTableName: string;
  removalPolicy?: RemovalPolicy;
}

export type StackyStatefulTablesStackProps = StackyStatefulTablesConfig & cdk.StackProps;

export class StackyStatefulTablesStack extends Stack {
  public readonly instrumentRunManagerTable: dynamodb.ITableV2;
  public readonly workflowManagerTable: dynamodb.ITableV2;
  public readonly inputGlueTable: dynamodb.ITableV2;
  public readonly cttsov2WorkflowGlueTable: dynamodb.ITableV2;
  public readonly wgtsQcGlueTable: dynamodb.ITableV2;
  constructor(scope: Construct, id: string, props: StackProps & StackyStatefulTablesStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where instrument_run_id is the single index key
    */
    this.instrumentRunManagerTable = new DynamodbPartitionedPipelineConstruct(
      this,
      'instrumentRunManagerTable',
      {
        tableName: props.dynamodbInstrumentRunManagerTableName,
        removalPolicy: props.removalPolicy,
      }
    ).tableObj;

    /*
    Initialise dynamodb table for the metadata manager
    */
    this.workflowManagerTable = new DynamodbPartitionedPipelineConstruct(
      this,
      'workflowManagerTable',
      {
        tableName: props.dynamodbWorkflowManagerTableName,
        removalPolicy: props.removalPolicy,
      }
    ).tableObj;

    /*
    Initialise dynamodb table for the glue services
    */
    this.inputGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'inputGlueTable', {
      tableName: props.dynamodbInputGlueTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the cttsov2 glue service
    */
    this.cttsov2WorkflowGlueTable = new DynamodbPartitionedPipelineConstruct(
      this,
      'cttsov2WorkflowGlueTable',
      {
        tableName: props.dynamodbCttsov2WorkflowGlueTableName,
        removalPolicy: props.removalPolicy,
      }
    ).tableObj;

    /*
    Initialise dynamodb table for the wgtsqc glue service
    */
    this.wgtsQcGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'wgtsQcGlueTable', {
      tableName: props.dynamodbWgtsQcGlueTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;
  }
}
