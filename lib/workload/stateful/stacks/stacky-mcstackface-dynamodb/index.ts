import { Stack, RemovalPolicy, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DynamodbPartitionedPipelineConstruct } from '../../../components/dynamodb-partitioned-table';
import * as cdk from 'aws-cdk-lib';

export interface StackyStatefulTablesConfig {
  dynamodbInstrumentRunManagerTableName: string;
  dynamodbCttsov2WorkflowGlueTableName: string;
  dynamodbWgtsQcGlueTableName: string;
  dynamodbTnGlueTableName: string;
  dynamodbWtsGlueTableName: string;
  dynamodbUmccriseGlueTableName: string;
  dynamodbRnasumGlueTableName: string;
  dynamodbPieriandxGlueTableName: string;
  dynamodbOncoanalyserGlueTableName: string;
  dynamodbOncoanalyserBothSashGlueTableName: string;
  removalPolicy?: RemovalPolicy;
}

export type StackyStatefulTablesStackProps = StackyStatefulTablesConfig & cdk.StackProps;

export class StackyStatefulTablesStack extends Stack {
  public readonly instrumentRunManagerTable: dynamodb.ITableV2;
  public readonly cttsov2WorkflowGlueTable: dynamodb.ITableV2;
  public readonly wgtsQcGlueTable: dynamodb.ITableV2;
  public readonly tnGlueTable: dynamodb.ITableV2;
  public readonly wtsGlueTable: dynamodb.ITableV2;
  public readonly umccriseGlueTable: dynamodb.ITableV2;
  public readonly rnasumGlueTable: dynamodb.ITableV2;
  public readonly pieriandxGlueTable: dynamodb.ITableV2;
  public readonly oncoanalyserGlueTable: dynamodb.ITableV2;
  public readonly oncoanalyserBothSashGlueTable: dynamodb.ITableV2;
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

    /*
    Initialise dynamodb table for the tn glue service
    */
    this.tnGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'tnGlueTable', {
      tableName: props.dynamodbTnGlueTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the wts glue service
    */
    this.wtsGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'wtsGlueTable', {
      tableName: props.dynamodbWtsGlueTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the umccrise glue service
    */
    this.umccriseGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'umccriseGlueTable', {
      tableName: props.dynamodbUmccriseGlueTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the rnasum glue service
    */
    this.rnasumGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'rnasumGlueTable', {
      tableName: props.dynamodbRnasumGlueTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the pieriandx glue service
    */
    this.pieriandxGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'pieriandxGlueTable', {
      tableName: props.dynamodbPieriandxGlueTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the oncoanalyser glue service
    */
    this.oncoanalyserGlueTable = new DynamodbPartitionedPipelineConstruct(
      this,
      'oncoanalyserGlueTable',
      {
        tableName: props.dynamodbOncoanalyserGlueTableName,
        removalPolicy: props.removalPolicy,
      }
    ).tableObj;

    /*
    Initialise dynamodb table for the oncoanalyser both + sash glue service
    */
    this.oncoanalyserBothSashGlueTable = new DynamodbPartitionedPipelineConstruct(
      this,
      'oncoanalyserBothSashGlueTable',
      {
        tableName: props.dynamodbOncoanalyserBothSashGlueTableName,
        removalPolicy: props.removalPolicy,
      }
    ).tableObj;
  }
}
