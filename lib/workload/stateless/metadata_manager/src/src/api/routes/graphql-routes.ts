import { FastifyInstance } from 'fastify';
import { fastifyHttpProxy } from '@fastify/http-proxy';

export const gqlRoutes = async (fastify: FastifyInstance) => {
  // GraphQL Experiment

  // edgedb with the extension of graphQL gives a graphQL endpoint.
  // The drawback of this endpoint is exposing the edgedb server to the world.
  // For now we would have a filter to deny any mutation through this graphql endpoint,
  // but in the future if we proceed with graphQL-ing we might need to
  // we might need a standalone GraphQL

  fastify.register(fastifyHttpProxy, {
    prefix: '/explore',
    upstream: 'http://localhost:10715/db/edgedb/graphql/explore',
    httpMethods: ['GET'],
    proxyPayloads: false,
  });

  fastify.register(fastifyHttpProxy, {
    upstream: 'http://localhost:10715/db/edgedb/graphql',
    httpMethods: ['POST'],
    proxyPayloads: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    preHandler: async (request: any, reply) => {
      // Reject graphql mutation request
      if (request.body['query'].startsWith('mutation')) {
        reply.code(400).send({ message: 'unable to support mutation through graphql' });
      }
    },
  });
};
