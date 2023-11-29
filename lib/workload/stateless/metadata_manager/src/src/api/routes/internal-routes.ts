import { FastifyInstance } from 'fastify';
import { DependencyContainer } from 'tsyringe';
import { MetadataService } from '../../service/metadata';

export const internalRoutes = async (
  fastify: FastifyInstance,
  opts: { container: DependencyContainer }
) => {
  const metadataService = opts.container.resolve(MetadataService);

  fastify.get('/library', async () => {
    return metadataService.getAllLibrary();
  });

  fastify.get('/specimen', async () => {
    return metadataService.getAllSpecimen();
  });

  fastify.get('/subject', async () => {
    return metadataService.getAllSubject();
  });
};
