import { Construct } from 'constructs';
import { EventBus } from 'aws-cdk-lib/aws-events';
import { Duration, Stack } from 'aws-cdk-lib';

export class EventBusConstruct extends Construct {

  public static readonly MAIN_BUS: string = 'OrcaBusMain';  // FIXME externalise config
  public static readonly MAIN_BUS_ARCHIVE: string = 'OrcaBusMainArchive';

  constructor(scope: Construct, id: string) {
    super(scope, id);
    this.createMainBus();
  }

  private createMainBus() {
    const mainBus = new EventBus(this, EventBusConstruct.MAIN_BUS, {
      eventBusName: EventBusConstruct.MAIN_BUS,
    });

    mainBus.archive(EventBusConstruct.MAIN_BUS_ARCHIVE, {
      archiveName: EventBusConstruct.MAIN_BUS_ARCHIVE,
      description: 'OrcaBus main event bus archive',
      eventPattern: {
        account: [Stack.of(this).account],
      },
      retention: Duration.days(365),
    });
  }
}
