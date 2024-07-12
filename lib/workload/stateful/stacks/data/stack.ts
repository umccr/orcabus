import { RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';

export interface DataBucketStackProps {
  /**
   * Bucket name that stored test/dev data
   */
  bucketName?: string;
}

/**
 * This Stack only gets deployed if bucketName is specified in the props
 */
export class DataBucketStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & DataBucketStackProps) {
    super(scope, id, props);

    if (props.bucketName) {
      new s3.Bucket(this, 'DataBucket', {
        bucketName: props.bucketName,
        autoDeleteObjects: true,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        enforceSSL: true,
        removalPolicy: RemovalPolicy.DESTROY,
      });
    }
  }
}
