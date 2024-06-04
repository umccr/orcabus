import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { RemovalPolicy } from 'aws-cdk-lib';

export interface DynamodbNonPartitionedPipelineConstructProps {
  tableName: string;
  removalPolicy?: RemovalPolicy;
}

export class DynamodbNonPartitionedPipelineConstruct extends Construct {
  public readonly tableObj: dynamodb.ITableV2;
  public readonly tableNameArn: string;

  constructor(scope: Construct, id: string, props: DynamodbNonPartitionedPipelineConstructProps) {
    super(scope, id);

    this.tableObj = new dynamodb.TableV2(this, 'dynamodb_partitioned_pipeline_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.tableName,
      removalPolicy: props.removalPolicy,
    });

    // Set outputs
    this.tableNameArn = this.tableObj.tableArn;
  }
}
