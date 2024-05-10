import { Stack, RemovalPolicy, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DynamodbIcav2PipelineConstruct } from '../../../../components/dynamodb-icav2-table';

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
    super(scope, id);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    new DynamodbIcav2PipelineConstruct(this, 'cttsov2_icav2_pipeline_table', {
      tableName: props.dynamodbTableName,
      removalPolicy: props.removalPolicy,
    });
  }
}
