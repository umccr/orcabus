import { Client } from 'edgedb';
import { DependencyContainer } from 'tsyringe';
import { Logger } from 'pino';
import { blankDb } from '../utils';
import { MetadataService } from '../../service/metadata';
import * as reader from 'xlsx';
import * as path from 'path';
import { MetadataGoogleService } from '../../service/loader-method/googleSheet';

const YEAR_START = 2018;
const YEAR_END = new Date().getFullYear();

export default async function insertScenario2(dc: DependencyContainer) {
  const logger = dc.resolve<Logger>('Logger');
  const metadataService = dc.resolve(MetadataService);
  const metadataGoogleService = dc.resolve(MetadataGoogleService);
  const edgeDbClient = dc.resolve<Client>('Database');

  logger.info('Blank database before inserting scenario-2');
  await blankDb(edgeDbClient);

  logger.info('inserting scenario 2 (based on `metadata.xlsx`)');
  const file = reader.readFile(path.join(__dirname, './metadata.xlsx'));

  let data = [];

  for (let index = YEAR_START; index <= YEAR_END; index++) {
    const sheetData = reader.utils.sheet_to_json(file.Sheets[index]);
    data = data.concat(sheetData);
  }

  const convertedRecord = metadataGoogleService.convertToMetadataRecord(data);

  // Updating Db
  await metadataService.upsertMetadataRecords(convertedRecord);
  await metadataService.removeDeletedMetadataRecords(convertedRecord);
}
