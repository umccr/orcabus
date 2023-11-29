import Fastify, { FastifyBaseLogger, FastifyInstance } from 'fastify';
import { DependencyContainer } from 'tsyringe';
import { internalRoutes } from './api/routes/internal-routes';
import { gqlRoutes } from './api/routes/graphql-routes';

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

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    this.server.addHook('onRequest', async (req, reply) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (req as any).container = this.dc;
    });
  }

  public async setupServer(): Promise<FastifyInstance> {
    // Register Fastify routing
    this.server.register(internalRoutes, {
      container: this.dc,
    });
    this.server.register(gqlRoutes, {
      container: this.dc,
      prefix: '/graphql',
    });

    return this.server;
  }
}
