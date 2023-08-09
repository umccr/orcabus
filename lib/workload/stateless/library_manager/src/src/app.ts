import Fastify, { FastifyBaseLogger, FastifyInstance } from 'fastify';
import e from '../dbschema/edgeql-js';
import { DependencyContainer } from 'tsyringe';
import { internalRoutes } from './api/routes/internal-routes';
import insertScenario1 from './test-data/scenario-1';
import { Client } from 'edgedb';

export class App {
  public readonly server: FastifyInstance;
  /**
   * @param dc
   */
  constructor(private readonly dc: DependencyContainer) {
    this.server = Fastify({
      logger: dc.resolve<FastifyBaseLogger>('Logger'),
    });

    // inject a copy of the Elsa settings and a custom child DI container into every Fastify request
    this.server.decorateRequest('container', null);

    this.server.addHook('onRequest', async (req, reply) => {
      (req as any).container = this.dc;
    });
  }

  public async setupServer(dc: DependencyContainer): Promise<FastifyInstance> {
    // register global fastify plugins
    // {
    // }
    const edgeDbClient = dc.resolve<Client>('Database');

    // WARNING: THIS IS DEV MODE
    await e.delete(e.metadata.Subject).run(edgeDbClient);
    await e.delete(e.metadata.Specimen).run(edgeDbClient);
    await e.delete(e.metadata.Library).run(edgeDbClient);

    await insertScenario1(dc);

    // Register Fastify routing
    {
      this.server.register(internalRoutes);
    }

    return this.server;
  }
}
