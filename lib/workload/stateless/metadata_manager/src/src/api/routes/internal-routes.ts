import { FastifyInstance } from 'fastify';
import { DependencyContainer } from 'tsyringe';

export const internalRoutes = async (
  fastify: FastifyInstance,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _opts: { container: DependencyContainer }
) => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  fastify.get('/hello', async (request, reply) => {
    return 'Hello World!\n';
  });
};
