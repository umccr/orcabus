import { Client, Duration, createClient } from 'edgedb';
import * as tsyringe from 'tsyringe';
import { SSMClient } from '@aws-sdk/client-ssm';
import { instanceCachingFactory } from 'tsyringe';
import pino, { Logger } from 'pino';
import { MetadataService } from '../service/metadata';
import { MetadataGoogleService } from '../service/loader-method/googleSheet';
import { getSecretManagerWithLayerExtension } from '../utils';

export async function createDependencyContainer() {
  const dc = tsyringe.container.createChildContainer();

  // Get the edge-db password from SM
  const edgeDbPassword = process.env.EDGEDB_SECRET_NAME
    ? await getSecretManagerWithLayerExtension(process.env.EDGEDB_SECRET_NAME)
    : undefined;

  dc.register<Client>('Database', {
    // https://www.edgedb.com/docs/clients/js/driver#configuring-clients
    useFactory: instanceCachingFactory(() =>
      createClient({
        password: edgeDbPassword,
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

  dc.register<SSMClient>('SSMClient', {
    useFactory: () => new SSMClient({}),
  });

  dc.registerSingleton(MetadataService);
  dc.registerSingleton(MetadataGoogleService);

  // Note: dependencies of class constructors must be injected manually when using esbuild.
  return dc;
}
