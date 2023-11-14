import { Client, Duration, createClient } from 'edgedb';
import * as tsyringe from 'tsyringe';
import { instanceCachingFactory } from 'tsyringe';
import pino, { Logger } from 'pino';
import { MetadataService } from '../service/metadata';
import { MetadataGoogleService } from '../service/loader-method/googleSheet';
import { getSecretManagerWithLayerExtension } from '../utils';

export async function createDependencyContainer() {
  const dc = tsyringe.container.createChildContainer();

  // Get the edge-db password from SM
  const edgeDbPassword = process.env.METADATA_MANAGER_EDGEDB_SECRET_NAME
    ? await getSecretManagerWithLayerExtension(process.env.METADATA_MANAGER_EDGEDB_SECRET_NAME)
    : undefined;

  dc.register<Client>('Database', {
    // https://www.edgedb.com/docs/clients/js/driver#configuring-clients
    useFactory: instanceCachingFactory(() =>
      createClient({
        host: process.env.EDGEDB_HOST ?? 'localhost',
        port: process.env.EDGEDB_PORT ? parseInt(process.env.EDGEDB_PORT) : 5656,
        database: process.env.EDGEDB_DATABASE ?? 'edgedb',
        tlsSecurity: 'insecure',
        password: edgeDbPassword ?? 'admin',
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

  dc.registerSingleton(MetadataService);
  dc.registerSingleton(MetadataGoogleService);

  return dc;
}
