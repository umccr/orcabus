import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import { RemovalPolicy } from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface DataSharingS3Config {
  bucketName: string;
  bucketPrefix?: string;
  tableName: string;
  removalPolicy?: RemovalPolicy;
}

export type DataSharingS3StackProps = DataSharingS3Config & cdk.StackProps;

export class DataSharingS3 extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DataSharingS3StackProps) {
    super(scope, id, props);

    /*
    Initialise s3 bucket
    Any user in the account can read and write to the bucket
    at the bucket prefix props.bucketPrefix
    */
    const bucket = new s3.Bucket(this, 'DataSharingS3', {
      // Generate bucket with the following name
      bucketName: props.bucketName,
      // Allow any user in the account to read at the bucket level
      accessControl: s3.BucketAccessControl.AUTHENTICATED_READ,
      // Delete bucket when stack is deleted
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // Add write options to the bucket prefix
    bucket.addToResourcePolicy(
      new iam.PolicyStatement({
        actions: ['s3:PutObject', 's3:GetObject'],
        resources: [bucket.arnForObjects(`${props.bucketPrefix ?? ''}*`)],
        principals: [new iam.AnyPrincipal()],
      })
    );

    // Data sharing db
    /* Create the fastq job table */
    new dynamodb.TableV2(this, 'data_sharing_object_dynamodb_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'object_type',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.tableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      globalSecondaryIndexes: [
        // Index for querying by steps execution id
        {
          indexName: 'steps_execution_id-index',
          partitionKey: {
            name: 'steps_execution_id',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'id',
            type: dynamodb.AttributeType.STRING,
          },
          projectionType: dynamodb.ProjectionType.INCLUDE,
          nonKeyAttributes: ['object_type'],
        },
      ],
    });
  }
}
