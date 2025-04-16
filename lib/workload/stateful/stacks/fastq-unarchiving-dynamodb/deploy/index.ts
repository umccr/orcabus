import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { RemovalPolicy } from 'aws-cdk-lib';

export interface FastqUnarchivingManagerTableConfig {
  /* DynamoDB table names */
  fastqUnarchivingJobDynamodbTableName: string;
  removalPolicy?: RemovalPolicy;
}

export type FastqUnarchivingManagerTableStackProps = FastqUnarchivingManagerTableConfig &
  cdk.StackProps;

export class FastqUnarchivingManagerTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props: FastqUnarchivingManagerTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table
    */
    this.initialise_dynamodb_table(props);
  }

  private initialise_dynamodb_table(props: FastqUnarchivingManagerTableStackProps) {
    /* Create the fastq job table */
    new dynamodb.TableV2(this, 'unarchiving_job_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.fastqUnarchivingJobDynamodbTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      globalSecondaryIndexes: [
        // Index for querying by status
        {
          indexName: 'status-index',
          partitionKey: {
            name: 'status',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['job_type', 'start_time', 'end_time'],
        },
        // Index for querying by job_type if we ever
        // generate services for other job types
        {
          indexName: 'job_type-index',
          partitionKey: {
            name: 'job_type',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['status', 'start_time', 'end_time'],
        },
      ],
    });
  }
}
