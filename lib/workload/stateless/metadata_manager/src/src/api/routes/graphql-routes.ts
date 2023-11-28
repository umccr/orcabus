import { FastifyInstance, FastifyRequest } from 'fastify';
import { fastifyHttpProxy } from '@fastify/http-proxy';

export const gqlRoutes = async (fastify: FastifyInstance) => {
  const graphQLEndpoint =
    `https://` +
    `${process.env.EDGEDB_HOST ?? 'localhost'}` +
    `:` +
    `${process.env.EDGEDB_PORT ?? 5656}` +
    `/db/` +
    `${process.env.EDGEDB_DATABASE ?? 'edgedb'}` +
    `/graphql`;

  fastify.register(fastifyHttpProxy, {
    prefix: '/explore',
    upstream: `${graphQLEndpoint}/explore`,
    httpMethods: ['GET'],
    proxyPayloads: false,
    preHandler: async (request: FastifyRequest) => {
      // It seems that fastify don't like if content-length == 0 while the body is undefined
      // (despite of a GET request) and load-balancer/API-Gateway adds this automatically
      // So, removing the 'content-length' to resolve this
      if (request.headers['content-length']) {
        delete request.headers['content-length'];
      }
    },
  });

  fastify.register(fastifyHttpProxy, {
    upstream: graphQLEndpoint,
    httpMethods: ['POST'],
    proxyPayloads: false,
    preHandler: async (request: FastifyRequest, reply) => {
      // We wanted to reject any kind of mutation via the GraphQL endpoint
      const body = request.body as Record<string, string> | undefined;
      if (body.query?.includes('mutation')) {
        reply
          .code(400)
          .send({ message: 'mutation is not supported through this graphql endpoint' });
      }
    },
  });
};
