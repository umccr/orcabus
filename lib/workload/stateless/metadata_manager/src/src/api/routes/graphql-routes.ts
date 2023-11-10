import { FastifyInstance, FastifyRequest } from 'fastify';
import { fastifyHttpProxy } from '@fastify/http-proxy';

export const gqlRoutes = async (fastify: FastifyInstance) => {
  const graphQLEndpoint =
    `https://` +
    `${process.env.EDGEDB_HOST ?? 'localhost'}` +
    `:` +
    `${process.env.EDGEDB_PORT ?? 10715}` +
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
      // Removing the 'content-length' to resolve issue
      if (request.headers['content-length']) {
        delete request.headers['content-length'];
      }
    },
  });

  fastify.register(fastifyHttpProxy, {
    upstream: graphQLEndpoint,
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
