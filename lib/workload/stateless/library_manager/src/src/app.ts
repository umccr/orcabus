import Fastify, { FastifyBaseLogger, FastifyInstance } from 'fastify';

import { DependencyContainer } from 'tsyringe';

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

  public async setupServer(): Promise<FastifyInstance> {
    // register global fastify plugins
    // {
    // }

    // Register Fastify routing
    {
      this.server.get('/ping', async (request, reply) => {
        return 'pong\n';
      });
    }

    return this.server;
  }
}
