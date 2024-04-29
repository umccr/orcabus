import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface DynamodbIcav2PipelineConstructProps {
  table_name: string;
}

export class DynamodbIcav2PipelineConstruct extends Construct {
  public readonly table_obj: dynamodb.ITableV2;
  public readonly table_name_arn: string;

  constructor(scope: Construct, id: string, props: DynamodbIcav2PipelineConstructProps) {
    super(scope, id);

    this.table_obj = new dynamodb.TableV2(this, 'dynamodb_icav2_pipeline_table', {
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
      tableName: props.table_name,
    });

    // Set outputs
    this.table_name_arn = this.table_obj.tableArn;
  }
}
