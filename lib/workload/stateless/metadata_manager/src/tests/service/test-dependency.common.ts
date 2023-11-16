import 'reflect-metadata';

import { container, instanceCachingFactory } from 'tsyringe';
import { Client, Duration, createClient } from 'edgedb';
import { Logger, pino } from 'pino';
import { SSMClient } from '@aws-sdk/client-ssm';

export function registerTypes() {
  const dc = container.createChildContainer();

  dc.register<Record<string, string>>('Settings', {
    useValue: {},
  });

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
