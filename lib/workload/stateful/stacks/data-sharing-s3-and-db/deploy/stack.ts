import * as cdk from 'aws-cdk-lib';
import { RemovalPolicy } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { AttributeType, ProjectionType } from 'aws-cdk-lib/aws-dynamodb';
import { NagSuppressions } from 'cdk-nag';

export interface DataSharingS3AndTableConfig {
  bucketName: string;
  bucketPrefix?: string;
  packagingApiTableName: string;
  pushJobApiTableName: string;
  packagingLookUpTableName: string;
  removalPolicy?: RemovalPolicy;
}

export type DataSharingS3AndTableStackProps = DataSharingS3AndTableConfig & cdk.StackProps;

export class DataSharingS3AndTableStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DataSharingS3AndTableStackProps) {
    super(scope, id, props);

    /*
    Initialise s3 bucket
    Any user in the account can read and write to the bucket
    at the bucket prefix props.bucketPrefix
    */
    const bucket = new s3.Bucket(this, 'DataSharingS3', {
      // Generate bucket with the following name
      bucketName: props.bucketName,
      // Delete bucket when stack is deleted
      removalPolicy: RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      // Enfore SSL
      enforceSSL: true,
    });

    // Add in S1 suppressions for the two buckets we've created
    NagSuppressions.addResourceSuppressions(
      [bucket],
      [
        {
          id: 'AwsSolutions-S1',
          reason: 'The bucket is not publicly accessible',
        },
      ],
      true
    );

    new dynamodb.TableV2(this, 'packaging_lookup_table', {
      /* An orcabus id of some type */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      /* 'job_id' */
      sortKey: {
        name: 'job_id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.packagingLookUpTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      // Enable TTL on the table
      timeToLiveAttribute: 'expire_at',
      globalSecondaryIndexes: [
        // Index for querying by job id plus the context type
        {
          indexName: 'context-index',
          partitionKey: {
            name: 'context',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: ProjectionType.INCLUDE,
          nonKeyAttributes: ['job_id'],
        },
        // Warning with the content-index a query may
        // exceed the 1MB limit - so you will need to
        // paginate
        {
          indexName: 'content-index',
          partitionKey: {
            name: 'context',
            type: AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: AttributeType.STRING,
          },
          projectionType: ProjectionType.INCLUDE,
          nonKeyAttributes: ['job_id', 'content', 'presigned_url', 'presigned_expiry'],
        },
      ],
    });

    // Data sharing db
    /* Create the packaging table */
    new dynamodb.TableV2(this, 'data_sharing_packaging_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.packagingApiTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      globalSecondaryIndexes: [
        // Index for querying by steps execution id
        {
          indexName: 'package_name-index',
          partitionKey: {
            name: 'package_name',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['status', 'request_time', 'completion_time'],
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
          nonKeyAttributes: ['package_name', 'request_time', 'completion_time'],
        },
      ],
    });

    /* Create the push job table */
    new dynamodb.TableV2(this, 'data_sharing_push_job_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.pushJobApiTableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      globalSecondaryIndexes: [
        // Index for querying
        {
          indexName: 'package_id-index',
          partitionKey: {
            name: 'package_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['package_name', 'status', 'start_time', 'end_time'],
        },
        {
          indexName: 'package_name-index',
          partitionKey: {
            name: 'package_name',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['package_id', 'status', 'start_time', 'end_time'],
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
          nonKeyAttributes: ['package_id', 'package_name', 'start_time', 'end_time'],
        },
      ],
    });
  }
}
