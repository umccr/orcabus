import { FastifyInstance } from 'fastify';
import { DependencyContainer } from 'tsyringe';
import { MetadataService } from '../../service/metadata';
import {
  selectAllLibraryQueryArgsSchema,
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
        query: selectAllLibraryQueryArgsSchema,
        response: {
          200: {
            description: 'Successful',
            type: 'object',
            properties: selectAllLibraryQueryReturnsSchema,
          },
        },
      },
    },
    async (req, res) => {
      return metadataService.getAllLibrary(req.query);
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
    async (req, res) => {
      return metadataService.getAllSpecimen(req.query);
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
    async (req, res) => {
      return metadataService.getAllSubject(req.query);
    }
  );
};
