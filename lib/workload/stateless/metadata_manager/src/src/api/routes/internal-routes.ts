import { z } from 'zod';
import { FastifyInstance } from 'fastify';
import { DependencyContainer } from 'tsyringe';
import { MetadataService } from '../../service/metadata';
import {
  selectAllLibraryQueryArgsSchema,
  selectAllLibraryQueryReturnsSchema,
  selectAllSpecimenQueryArgsSchema,
  selectAllSpecimenQueryReturnsSchema,
  selectAllSubjectQueryArgsSchema,
  selectAllSubjectQueryReturnsSchema,
} from '../../../dbschema/queriesZodSchema';

/**
 * Query parameter only accept string where pagination needs to be number, this function will
 * add coerce to zod schema to convert these pagination value to numbers
 *
 * @param zodSchema The raw ZodSchema (that is not coerce)
 * @returns
 */

const coercePaginationType = <Z extends z.ZodObject<any>>(zodSchema: Z) => {
  const paginationSchema = z.object({
    offset: z.coerce.number().optional().nullable(),
    limit: z.coerce.number().optional().nullable(),
  });

  return zodSchema.omit({ offset: true, limit: true }).merge(paginationSchema);
};

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
        query: coercePaginationType(selectAllLibraryQueryArgsSchema),
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
        query: coercePaginationType(selectAllSpecimenQueryArgsSchema),
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
        query: coercePaginationType(selectAllSubjectQueryArgsSchema),
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
