import { Construct } from 'constructs';
import { Duration, Stack } from 'aws-cdk-lib';
import * as events from 'aws-cdk-lib/aws-events';

export interface EventBusProps {
  eventBusName: string;
  archiveName: string;
  archiveDescription: string;
  archiveRetention: number;
}

export class EventBusConstruct extends Construct {
  readonly mainBus: events.EventBus;

  constructor(scope: Construct, id: string, props: EventBusProps) {
    super(scope, id);
    this.mainBus = this.createMainBus(props);
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
}
