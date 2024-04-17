import { Construct } from 'constructs';
import { Duration, Stack } from 'aws-cdk-lib';
import * as events from 'aws-cdk-lib/aws-events';
import { Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { UniversalEventArchiverConstruct } from './custom-event-archiver/construct/universal-event-archiver';

export interface EventBusProps {
  eventBusName: string;
  archiveName: string;
  archiveDescription: string;
  archiveRetention: number;

  // Optional for custom event archiver
  addCustomEventArchiver?: boolean;
  vpc?: VpcLookupOptions;
  archiveBucket?: string;
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
    if (!props.vpc || !props.archiveBucket) {
      throw new Error('VPC and Archive Bucket are required for custom event archiver');
    }
    const archiveBucket = Bucket.fromBucketName(this, 'AuditBucket', props.archiveBucket);
    const vpc = Vpc.fromLookup(this, 'MainVpc', props.vpc);

    new UniversalEventArchiverConstruct(this, 'UniversalEventArchiver', {
      vpc,
      archiveBucket,
      eventBus: this.mainBus,
    });
  }
}
