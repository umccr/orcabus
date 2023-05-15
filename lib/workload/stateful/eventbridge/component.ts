import { Construct } from 'constructs';
import { EventBus } from 'aws-cdk-lib/aws-events';
import { Duration, Stack } from 'aws-cdk-lib';

export interface EventBusProps {
  eventBusName: string;
  archiveName: string;
  archiveDescription: string;
  archiveRetention: number;
}

export class EventBusConstruct extends Construct {
  constructor(scope: Construct, id: string, props: EventBusProps) {
    super(scope, id);
    this.createMainBus(props);
  }

  private createMainBus(props: EventBusProps) {
    const mainBus = new EventBus(this, props.eventBusName, {
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
  }
}
