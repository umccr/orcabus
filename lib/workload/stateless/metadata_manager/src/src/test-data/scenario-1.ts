import { DependencyContainer } from 'tsyringe';
import { Logger } from 'pino';
import { MetadataGoogleService } from '../service/loader-method/googleSheet';
import { METADATA_GOOGLE_OBJ } from '../../tests/service/gsheet.common';

export default async function insertScenario1(dc: DependencyContainer) {
  const logger = dc.resolve<Logger>('Logger');
  const gService = dc.resolve(MetadataGoogleService);

  logger.info('inserting scenario 1');
  await gService.upsertGoogleMetadataRecords(METADATA_GOOGLE_OBJ);
}
