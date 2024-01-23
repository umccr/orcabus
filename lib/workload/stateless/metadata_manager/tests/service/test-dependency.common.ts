import 'reflect-metadata';

import { container, instanceCachingFactory } from 'tsyringe';
import { Client, Duration, createClient } from 'edgedb';
import { Logger, pino } from 'pino';

export function registerTypes() {
  const dc = container.createChildContainer();

  dc.register<Record<string, string>>('Settings', {
    useValue: {},
  });

  dc.register<Client>('Database', {
    // https://www.edgedb.com/docs/clients/js/driver#configuring-clients
    useFactory: instanceCachingFactory(() =>
      createClient({
        host: process.env.EDGEDB_HOST ?? 'localhost',
        port: process.env.EDGEDB_PORT ? parseInt(process.env.EDGEDB_PORT) : 5656,
        database: process.env.EDGEDB_DATABASE ?? 'edgedb',
        tlsSecurity: 'insecure',
        password: 'admin', // pragma: allowlist secret
        user: process.env.EDGEDB_USER ?? 'orcabus_admin',
      }).withConfig({
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

  return dc;
}
