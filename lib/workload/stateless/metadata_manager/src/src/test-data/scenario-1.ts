import { Client } from 'edgedb';
import { DependencyContainer } from 'tsyringe';
import { Logger } from 'pino';
import { blankDb } from './utils';
import { MetadataService } from '../service/metadata';
import { METADATA_REC_ARR } from '../../tests/service/metadata.common';

export default async function insertScenario1(dc: DependencyContainer) {
  const logger = dc.resolve<Logger>('Logger');
  const metadataService = dc.resolve(MetadataService);
  const edgeDbClient = dc.resolve<Client>('Database');

  logger.info('Blank database before inserting scenario-1');
  await blankDb(edgeDbClient);

  logger.info('inserting scenario 1');
  await metadataService.upsertMetadataRecords(METADATA_REC_ARR);
}
