import { registerTypes } from './test-dependency.common';
import { MetadataGoogleService } from '../../src/service/loader-method/googleSheet';
import { METADATA_GOOGLE_OBJ } from './gsheet.common';
import { Client } from 'edgedb';
import { resetDb } from './utils';
import { isEqual } from 'lodash';

const testContainer = registerTypes();
let edgeDbClient: Client;
let gService: MetadataGoogleService;

describe('sync metadata from google spreadsheet', () => {
  beforeAll(async () => {
    gService = testContainer.resolve(MetadataGoogleService);
    edgeDbClient = testContainer.resolve('Database');
  });

  beforeEach(async () => {
    await resetDb(edgeDbClient);
    // jest.useFakeTimers();
  });

  // afterEach(async () => {});

  // it('Test download google sheet to object', async () => {
  //   const val = await gService.getSheetObject('2022');

  //   const firstRow = val[0];
  //   console.log('firstRow', firstRow);

  //   // console.log('val', val.reverse().slice(0, 5));
  //   // console.log('length', val.length);
  // });
  it('test sync function to insert new record', async () => {
    const val = await gService.syncGoogleMetadataRecords(METADATA_GOOGLE_OBJ);

    // console.log('val', val.reverse().slice(0, 5));
    // console.log('length', val.length);
  });
});
