import Fastify, { FastifyBaseLogger, FastifyInstance } from 'fastify';
import fastifySwagger from '@fastify/swagger';
import fastifySwaggerUi from '@fastify/swagger-ui';
import { DependencyContainer } from 'tsyringe';
import { internalRoutes } from './api/routes/internal-routes';
import { gqlRoutes } from './api/routes/graphql-routes';
import { SettingType } from './bootstrap/settings';

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
    // OpenAPI
    await this.server.register(fastifySwagger, {
      // openapi 3.0.3 options
      openapi: {
        info: {
          title: 'OrcaBus - Metadata Manager',
          description: 'one of the microservice in OrcaBus that handles on metadata',
          version: '0.0.1',
          license: { name: 'MIT License' },
        },
        components: {
          securitySchemes: {
            apiKey: {
              type: 'apiKey',
              name: 'Authorization',
              in: 'header',
            },
          },
        },
      },
      hideUntagged: true,
    });
    await this.server.register(fastifySwaggerUi, {
      routePrefix: '/documentation',
      uiConfig: {
        docExpansion: 'full',
        deepLinking: false,
      },
    });

    // Register API Routing for the app
    await this.server.register(internalRoutes, {
      container: this.dc,
    });
    await this.server.register(gqlRoutes, {
      container: this.dc,
      prefix: '/graphql',
    });

    return this.server;
  }
}
