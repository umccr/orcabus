import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface ICAv2EventTranslatorDynamoDBTableConstructProps {
  icav2EventTranslatorDynamodbTableName: string;
}
export class ICAv2EventTranslatorDynamoDBTableConstruct extends Construct {
  readonly icav2EventTranslatorDynamodbTable: dynamodb.Table;
  constructor(
    scope: Construct,
    id: string,
    props: ICAv2EventTranslatorDynamoDBTableConstructProps
  ) {
    super(scope, id);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    this.icav2EventTranslatorDynamodbTable = this.createDynamoDBTable(props);
  }

  private createDynamoDBTable(props: ICAv2EventTranslatorDynamoDBTableConstructProps) {
    return new dynamodb.Table(this, 'ICAv2EventTranslatorDynamoDBTable', {
      tableName: props.icav2EventTranslatorDynamodbTableName,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      /* Either a db_uuid or an icav2 event id or a portal run id */
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'id_type', type: dynamodb.AttributeType.STRING },
    });
  }
}
