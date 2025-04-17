import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { RemovalPolicy } from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { NagSuppressions } from 'cdk-nag';

export interface FastqManagerTableConfig {
  /* DynamoDB table names */
  fastqListRowDynamodbTableName: string;
  fastqSetDynamodbTableName: string;
  fastqJobDynamodbTableName: string;
  /* Buckets */
  ntsmBucketName: string;
  fastqManagerCacheBucketName: string;
  removalPolicy?: RemovalPolicy;
}

export type FastqManagerTableStackProps = FastqManagerTableConfig & cdk.StackProps;

export class FastqManagerTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props: FastqManagerTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table
    */
    this.initialise_dynamodb_tables(props);

    /*
    Add buckets
    */
    this.add_buckets(props);
  }

  private initialise_dynamodb_tables(props: FastqManagerTableStackProps) {
    new dynamodb.TableV2(this, 'fastq_manager_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.fastqListRowDynamodbTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
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
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['library_orcabus_id', 'instrument_run_id', 'fastq_set_id', 'is_valid'],
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
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['rgid_ext', 'instrument_run_id', 'fastq_set_id', 'is_valid'],
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
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: [
            'rgid_ext',
            'library_orcabus_id',
            'fastq_set_id',
            'is_valid',
            'index',
            'lane',
          ],
        },
        {
          indexName: 'fastq_set_id-index',
          partitionKey: {
            name: 'fastq_set_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['rgid_ext', 'library_orcabus_id', 'instrument_run_id', 'is_valid'],
        },
      ],
    });

    /* Create the fastq set table */
    new dynamodb.TableV2(this, 'fastq_set_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.fastqSetDynamodbTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      globalSecondaryIndexes: [
        // Index for querying by rgid_ext, library_orcabus_id and instrument_run_id
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
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['is_current_fastq_set', 'allow_additional_fastq'],
        },
      ],
    });

    /* Create the fastq job table */
    new dynamodb.TableV2(this, 'fastq_job_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.fastqJobDynamodbTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      globalSecondaryIndexes: [
        // Index for querying by fastq_id, job_type and status
        {
          indexName: 'fastq_id-index',
          partitionKey: {
            name: 'fastq_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['job_type', 'status'],
        },
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
          nonKeyAttributes: ['fastq_id', 'status'],
        },
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
          nonKeyAttributes: ['fastq_id', 'job_type'],
        },
      ],
    });
  }

  private add_buckets(props: FastqManagerTableStackProps) {
    // Add the ntsm bucket with event bridge enabled
    const ntsmBucket = new s3.Bucket(this, 'ntsm_bucket', {
      bucketName: props.ntsmBucketName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      eventBridgeEnabled: true, // So that the filemanager can listen to events
      enforceSSL: true,
    });

    // Add fastq manager cache bucket
    const fastqManagerCacheBucket = new s3.Bucket(this, 'fastq_manager_cache_bucket', {
      bucketName: props.fastqManagerCacheBucketName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      enforceSSL: true,
    });

    // Add in global cdk nag suppressions
    NagSuppressions.addStackSuppressions(
      this,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'We have no control over the BucketNotificationsHandler',
        },
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'We have no control over the BucketNotificationsHandler that uses an AWS managed policy',
        },
      ],
      true
    );

    // Add in S1 suppressions for the two buckets we've created
    NagSuppressions.addResourceSuppressions(
      [ntsmBucket, fastqManagerCacheBucket],
      [
        {
          id: 'AwsSolutions-S1',
          reason: 'The bucket is not publicly accessible and does not contain any sensitive data',
        },
      ],
      true
    );
  }
}
