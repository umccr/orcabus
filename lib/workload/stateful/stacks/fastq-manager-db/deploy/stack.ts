import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { RemovalPolicy } from 'aws-cdk-lib';

export interface FastqManagerTableConfig {
  dynamodbTableName: string;
  removalPolicy?: RemovalPolicy;
}

export type FastqManagerTableStackProps = FastqManagerTableConfig & cdk.StackProps;

export class FastqManagerTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props: FastqManagerTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table
    */
    const tableObj = new dynamodb.TableV2(this, 'fastq_manager_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.dynamodbTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecovery: true,
      globalSecondaryIndexes: [
        // Index for querying by rgid_ext, library_orcabus_id and instrument_run_id
        {
          indexName: 'rgid_ext-index',
          partitionKey: {
            name: 'rgid_ext',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.KEYS_ONLY,
        },
        {
          indexName: 'library_orcabus_id-index',
          partitionKey: {
            name: 'library_orcabus_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.KEYS_ONLY,
        },
        {
          indexName: 'instrument_run_id-index',
          partitionKey: {
            name: 'instrument_run_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.KEYS_ONLY,
        },
      ],
    });
  }
}
