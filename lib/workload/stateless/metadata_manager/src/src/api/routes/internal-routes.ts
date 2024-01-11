import { FastifyInstance } from 'fastify';
import { DependencyContainer } from 'tsyringe';
import { MetadataService } from '../../service/metadata';
import {
  selectAllLibraryQueryReturnsSchema,
  selectAllSpecimenQueryReturnsSchema,
  selectAllSubjectQueryReturnsSchema,
} from '../../../dbschema/queriesZodSchema';

export const internalRoutes = async (
  fastify: FastifyInstance,
  opts: { container: DependencyContainer }
) => {
  const metadataService = opts.container.resolve(MetadataService);

  fastify.get(
    '/library',
    {
      schema: {
        tags: ['library'],
        response: {
          200: {
            description: 'Successful',
            type: 'object',
            properties: selectAllLibraryQueryReturnsSchema,
          },
        },
      },
    },
    async () => {
      return metadataService.getAllLibrary();
    }
  );

  fastify.get(
    '/specimen',
    {
      schema: {
        tags: ['specimen'],
        response: {
          200: {
            description: 'Successful',
            type: 'object',
            properties: selectAllSpecimenQueryReturnsSchema,
          },
        },
      },
    },
    async () => {
      return metadataService.getAllSpecimen();
    }
  );

  fastify.get(
    '/subject',
    {
      schema: {
        tags: ['subject'],
        response: {
          200: {
            description: 'Successful',
            type: 'object',
            properties: selectAllSubjectQueryReturnsSchema,
          },
        },
      },
    },
    async () => {
      return metadataService.getAllSubject();
    }
  );
};
