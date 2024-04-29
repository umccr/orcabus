import { Construct } from 'constructs';
import { Duration, RemovalPolicy, Stack } from 'aws-cdk-lib';
import * as events from 'aws-cdk-lib/aws-events';
import { Vpc, VpcLookupOptions, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { UniversalEventArchiverConstruct } from './custom-event-archiver/construct/universal-event-archiver';

// generic event bus archiver props
export interface EventBusArchiverProps {
  vpcProps: VpcLookupOptions;
  lambdaSecurityGroupName: string;
  archiveBucketName: string;
  bucketRemovalPolicy: RemovalPolicy;
}

export interface EventBusProps {
  eventBusName: string;
  archiveName: string;
  archiveDescription: string;
  archiveRetention: number;

  // Optional for custom event archiver
  addCustomEventArchiver?: boolean;
  universalEventArchiverProps?: EventBusArchiverProps;
}

export class EventBusConstruct extends Construct {
  readonly mainBus: events.EventBus;

  constructor(scope: Construct, id: string, props: EventBusProps) {
    super(scope, id);
    this.mainBus = this.createMainBus(props);

    // Optional for custom event archiver
    if (props.addCustomEventArchiver) {
      props.universalEventArchiverProps &&
        this.createUniversalEventArchiver(props.universalEventArchiverProps);
    }
  }

  private createMainBus(props: EventBusProps) {
    const mainBus = new events.EventBus(this, props.eventBusName, {
      eventBusName: props.eventBusName,
    });

    mainBus.archive(props.archiveName, {
      archiveName: props.archiveName,
      description: props.archiveDescription,
      eventPattern: {
        account: [Stack.of(this).account],
      },
      retention: Duration.days(props.archiveRetention),
    });

    return mainBus;
  }

  private createUniversalEventArchiver(props: EventBusArchiverProps) {
    const vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);

    // dedicated bucket for archiving all events
    const archiveBucket = new Bucket(this, 'UniversalEventArchiveBucket', {
      bucketName: props.archiveBucketName,
      removalPolicy: props.bucketRemovalPolicy,
      enforceSSL: true, //denies any request made via plain HTTP
    });
    // dedicated security group for the lambda function
    const lambdaSG = new SecurityGroup(this, 'UniversalEventArchiverLambdaSG', {
      vpc,
      securityGroupName: props.lambdaSecurityGroupName,
      allowAllOutbound: true,
      description: 'Security group for the Universal Event Archiver Lambda function to egress out.',
    });

    new UniversalEventArchiverConstruct(this, 'UniversalEventArchiver', {
      vpc,
      lambdaSG,
      archiveBucket,
      eventBus: this.mainBus,
    });
  }
}
