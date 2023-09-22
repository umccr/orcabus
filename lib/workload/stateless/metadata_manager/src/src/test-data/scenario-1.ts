import { DependencyContainer } from 'tsyringe';
import { Logger } from 'pino';
import { MetadataService } from '../service/metadata';
import { METADATA_REC_ARR } from '../../tests/service/metadata.common';

export default async function insertScenario1(dc: DependencyContainer) {
  const logger = dc.resolve<Logger>('Logger');
  const metadataService = dc.resolve(MetadataService);

  logger.info('inserting scenario 1');
  metadataService.upsertMetadataRecords(METADATA_REC_ARR);
}
