import { Stack, RemovalPolicy, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import {DynamodbPartitionedPipelineConstruct} from "../../../components/dynamodb-partitioned-table";
import {DynamodbNonPartitionedPipelineConstruct} from "../../../components/dynamodb-nonpartitioned-table";


export interface stackyStatefulTablesProps {
  dynamodbInstrumentRunManagerTableName: string;
  dynamodbMetadataManagerTableName: string;
  dynamodbInputGlueTableName: string;
  removalPolicy?: RemovalPolicy;
}

export class stackyStatefulTablesConstruct extends Stack {
  public readonly instrumentRunManagerTable: dynamodb.ITableV2
  public readonly metadataManagerTable: dynamodb.ITableV2
  public readonly inputGlueTable: dynamodb.ITableV2
  constructor(
    scope: Construct,
    id: string,
    props: StackProps & stackyStatefulTablesProps
  ) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where instrument_run_id is the single index key
    */
    this.instrumentRunManagerTable = new DynamodbNonPartitionedPipelineConstruct(this, 'instrumentRunManagerTable', {
      tableName: props.dynamodbInstrumentRunManagerTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the metadata manager
    */
    this.metadataManagerTable = new DynamodbPartitionedPipelineConstruct(this, 'metadataManagerTable', {
      tableName: props.dynamodbInstrumentRunManagerTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;

    /*
    Initialise dynamodb table for the glue services
    */
    this.inputGlueTable = new DynamodbPartitionedPipelineConstruct(this, 'inputGlueTable', {
      tableName: props.dynamodbInstrumentRunManagerTableName,
      removalPolicy: props.removalPolicy,
    }).tableObj;
  }
}
