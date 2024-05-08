import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { IcaEventPipeConstruct, IcaEventPipeConstructProps } from './constructs/ica_event_pipe';
import { VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { RemovalPolicy } from 'aws-cdk-lib';
import { TableV2, AttributeType } from 'aws-cdk-lib/aws-dynamodb';
import {
  Icav2EventTranslatorConstructProps,
  IcaEventTranslatorConstruct,
} from './ica-event-translator/construct';

const alarmThreshod: number = 1;
const queueVizTimeout: number = 30;

export interface IcaEventTranslatorProps {
  /** dynamodb table for translator service */
  icav2EventTranslatorDynamodbTableName: string;
  removalPolicy?: RemovalPolicy;

  /** vpc ann SG for translator lambda function */
  vpcProps: VpcLookupOptions;
  lambdaSecurityGroupName: string;
}
/**
 * IcaEventPipeStackProps
 */
export interface IcaEventPipeStackProps {
  /** The name for stack */
  name: string;
  /** The name of the Event Bus to forward events to (used to lookup the Event Bus) */
  eventBusName: string;
  /** The name of the SNS Topic to receive DLQ notifications from CloudWatch */
  slackTopicName: string;
  /** The ICA account to grant publish permissions to */
  icaAwsAccountNumber: string;

  /** IcaEventTranslatorProps */
  IcaEventTranslatorProps: IcaEventTranslatorProps;
}

export class IcaEventPipeStack extends Stack {
  private readonly icaEventPipe: IcaEventPipeConstruct;

  constructor(scope: Construct, id: string, props: StackProps & IcaEventPipeStackProps) {
    super(scope, id, props);
    this.icaEventPipe = this.createPipeConstruct(this, 'IcaEventPipeConstruct', props);
    this.createIcaEventTranslator(props, this.icaEventPipe.pipe.pipeName);
  }

  private createPipeConstruct(
    scope: Construct,
    id: string,
    props: StackProps & IcaEventPipeStackProps
  ) {
    const constructProps: IcaEventPipeConstructProps = {
      icaEventPipeName: props.name + 'Pipe',
      icaQueueName: props.name + 'Queue',
      icaQueueVizTimeout: queueVizTimeout,
      eventBusName: props.eventBusName,
      dlqMessageThreshold: alarmThreshod,
      slackTopicArn: this.constructTopicArn(props),
      icaAwsAccountNumber: props.icaAwsAccountNumber,
    };
    return new IcaEventPipeConstruct(scope, id, constructProps);
  }

  private createIcaEventTranslator(props: IcaEventPipeStackProps, IcaEventPipeName: string) {
    // extract the IcaEventTranslatorConstructProps
    const icaEventTranslatorProps = props.IcaEventTranslatorProps;

    // create the dynamodb table for the translator service
    const eventTranslatorDynamoDBTable = new TableV2(this, 'ICAv2EventTranslatorDynamoDBTable', {
      tableName: icaEventTranslatorProps.icav2EventTranslatorDynamodbTableName,
      removalPolicy: icaEventTranslatorProps.removalPolicy || RemovalPolicy.DESTROY,

      /* Either a db_uuid or an icav2 event id or a portal run id */
      partitionKey: { name: 'analysis_id', type: AttributeType.STRING },
      sortKey: { name: 'event_status', type: AttributeType.STRING },
    });

    const icaEventTranslatorConstructProps: Icav2EventTranslatorConstructProps = {
      icav2EventTranslatorDynamodbTable: eventTranslatorDynamoDBTable,
      eventBusName: props.eventBusName,
      vpcProps: icaEventTranslatorProps.vpcProps,
      lambdaSecurityGroupName: icaEventTranslatorProps.lambdaSecurityGroupName,
      icaEventPipeName: IcaEventPipeName,
    };

    return new IcaEventTranslatorConstruct(
      this,
      'IcaEventTranslatorConstruct',
      icaEventTranslatorConstructProps
    );
  }

  private constructTopicArn(props: StackProps & IcaEventPipeStackProps) {
    if (!props.env) {
      throw new Error('No env properties found. Please ensure env.account and evn.region are set.');
    }
    if (!props.env.account) {
      throw new Error('No account');
    }
    if (!props.env.region) {
      throw new Error('No region');
    }
    return 'arn:aws:sns:' + props.env.region + ':' + props.env.account + ':' + props.slackTopicName;
  }
}
