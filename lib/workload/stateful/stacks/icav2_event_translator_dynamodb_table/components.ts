import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { TableV2, AttributeType } from 'aws-cdk-lib/aws-dynamodb';

export interface ICAv2EventTranslatorDynamoDBTableConstructProps {
  icav2EventTranslatorDynamodbTableName: string;
}
export class ICAv2EventTranslatorDynamoDBTableConstruct extends Construct {
  readonly icav2EventTranslatorDynamodbTable: TableV2;

  constructor(
    scope: Construct,
    id: string,
    props: ICAv2EventTranslatorDynamoDBTableConstructProps
  ) {
    super(scope, id);

    /*
    Initialise dynamodb table, where icav2_analysis_id is the primary sort key
    */
    this.icav2EventTranslatorDynamodbTable = this.createDynamoDBTable(props);
  }

  private createDynamoDBTable(props: ICAv2EventTranslatorDynamoDBTableConstructProps) {
    return new TableV2(this, 'ICAv2EventTranslatorDynamoDBTable', {
      tableName: props.icav2EventTranslatorDynamodbTableName,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      /* Either a db_uuid or an icav2 event id or a portal run id */
      partitionKey: { name: 'id', type: AttributeType.STRING },
      sortKey: { name: 'id_type', type: AttributeType.STRING },
    });
  }
}
