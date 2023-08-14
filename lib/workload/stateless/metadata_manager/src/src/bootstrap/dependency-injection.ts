import { Client, Duration, createClient } from 'edgedb';
import * as tsyringe from 'tsyringe';
import { SSMClient } from '@aws-sdk/client-ssm';
import { instanceCachingFactory } from 'tsyringe';
import pino, { Logger } from 'pino';

export async function createDependencyContainer() {
  const dc = tsyringe.container.createChildContainer();

  dc.register<Client>('Database', {
    // https://www.edgedb.com/docs/clients/js/driver#configuring-clients
    useFactory: instanceCachingFactory(() =>
      createClient().withConfig({
        session_idle_transaction_timeout: Duration.from({ seconds: 60 }),
      })
    ),
  });

  dc.register<Logger>('Logger', {
    useValue: pino({
      transport: {
        target: 'pino-pretty',
      },
    }),
  });

  dc.register<SSMClient>('SSMClient', {
    useFactory: () => new SSMClient({}),
  });

  // Note: dependencies of class constructors must be injected manually when using esbuild.
  return dc;
}
