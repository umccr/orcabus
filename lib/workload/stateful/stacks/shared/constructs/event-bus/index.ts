import { Construct } from 'constructs';
import { Duration, RemovalPolicy, Stack } from 'aws-cdk-lib';
import * as events from 'aws-cdk-lib/aws-events';
import { Vpc, VpcLookupOptions, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { UniversalEventArchiverConstruct } from './custom-event-archiver/construct/universal-event-archiver';

export interface EventBusProps {
  eventBusName: string;
  archiveName: string;
  archiveDescription: string;
  archiveRetention: number;

  // Optional for custom event archiver
  addCustomEventArchiver?: boolean;
  vpcProps?: VpcLookupOptions;
  lambdaSecurityGroupName?: string;
  archiveBucketName?: string;
}

export class EventBusConstruct extends Construct {
  readonly mainBus: events.EventBus;

  constructor(scope: Construct, id: string, props: EventBusProps) {
    super(scope, id);
    this.mainBus = this.createMainBus(props);

    // Optional for custom event archiver
    if (props.addCustomEventArchiver) {
      this.createUniversalEventArchiver(props);
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

  private createUniversalEventArchiver(props: EventBusProps) {
    if (!props.vpcProps || !props.archiveBucketName || !props.lambdaSecurityGroupName) {
      throw new Error(
        'VPC, Security Group and Archive Bucket are required for custom event archiver function.'
      );
    }

    const vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);

    // dedicated bucket for archiving all events
    const archiveBucket = new Bucket(this, 'UniversalEventArchiveBucket', {
      bucketName: props.archiveBucketName,
      removalPolicy: RemovalPolicy.RETAIN,
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
