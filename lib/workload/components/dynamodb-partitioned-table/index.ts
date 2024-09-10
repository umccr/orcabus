import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { RemovalPolicy } from 'aws-cdk-lib';

export interface DynamodbPartitionedPipelineConstructProps {
  tableName: string;
  removalPolicy?: RemovalPolicy;
}

export class DynamodbPartitionedPipelineConstruct extends Construct {
  public readonly tableObj: dynamodb.ITableV2;
  public readonly tableNameArn: string;

  constructor(scope: Construct, id: string, props: DynamodbPartitionedPipelineConstructProps) {
    super(scope, id);

    this.tableObj = new dynamodb.TableV2(this, 'dynamodb_partitioned_pipeline_table', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      /* One of 'db_uuid', 'icav2_analysis_id', 'portal_run_id' */
      sortKey: {
        name: 'id_type',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: props.tableName,
      removalPolicy: props.removalPolicy || RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
      pointInTimeRecovery: true,
    });

    // Set outputs
    this.tableNameArn = this.tableObj.tableArn;
  }
}
