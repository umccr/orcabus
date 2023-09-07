import { DependencyContainer } from 'tsyringe';
import e from '../../dbschema/edgeql-js';
import { Client } from 'edgedb';
import { Logger } from 'pino';
import { MetadataGoogleService } from '../service/loader-method/googleSheet';
import { METADATA_GOOGLE_OBJ } from '../../tests/service/gsheet.common';

export default async function insertScenario1(dc: DependencyContainer) {
  const edgeDbClient = dc.resolve<Client>('Database');
  const logger = dc.resolve<Logger>('Logger');
  const gService = dc.resolve(MetadataGoogleService);

  logger.info('inserting scenario 1');
  await gService.syncGoogleMetadataRecords(METADATA_GOOGLE_OBJ);
}
