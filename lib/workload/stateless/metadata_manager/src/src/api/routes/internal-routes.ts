import { FastifyInstance } from 'fastify';
import { DependencyContainer } from 'tsyringe';

export const internalRoutes = async (
  fastify: FastifyInstance,
  _opts: { container: DependencyContainer }
) => {
  fastify.get('/hello', async (request, reply) => {
    return 'Hello World!\n';
  });
};
