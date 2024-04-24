import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { TableV2, AttributeType } from 'aws-cdk-lib/aws-dynamodb';

export interface ICAv2EventTranslatorDynamodbTableConstructProps {
  icav2EventTranslatorDynamodbTableName: string;
  partitionKeyName: string; // icav2 analysis id
  sortKeyName: string; // icav2 analysis id
}

export interface DynamoDBTablesConstructProps {
  ICAv2EventTranslatorDynamoDBTableProps: ICAv2EventTranslatorDynamodbTableConstructProps;
}

export class DynamoDBTablesConstruct extends Construct {
  readonly icav2EventTranslatorDynamodbTable: TableV2;

  constructor(scope: Construct, id: string, props: DynamoDBTablesConstructProps) {
    super(scope, id);

    /*
    Initialise dynamodb table, where icav2_analysis_id is the primary sort key
    */
    this.icav2EventTranslatorDynamodbTable = this.createICAv2EventTranslatorDynamoDBTable(
      props.ICAv2EventTranslatorDynamoDBTableProps
    );
  }

  private createICAv2EventTranslatorDynamoDBTable(
    props: ICAv2EventTranslatorDynamodbTableConstructProps
  ) {
    return new TableV2(this, 'ICAv2EventTranslatorDynamoDBTable', {
      tableName: props.icav2EventTranslatorDynamodbTableName,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      /* Either a db_uuid or an icav2 event id or a portal run id */
      partitionKey: { name: props.partitionKeyName, type: AttributeType.STRING },
      sortKey: { name: props.sortKeyName, type: AttributeType.STRING },
    });
  }
}
