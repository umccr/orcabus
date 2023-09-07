import e from '../../dbschema/edgeql-js';
import { registerTypes } from './test-dependency.common';
import { MetadataGoogleService } from '../../src/service/loader-method/googleSheet';
import {
  METADATA_GOOGLE_OBJ,
  METADATA_REC_1,
  METADATA_REC_2,
  METADATA_REC_4,
} from './gsheet.common';
import { Client } from 'edgedb';
import { resetDb } from './utils';

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

  it('libraries with the same specimen', async () => {
    await gService.syncGoogleMetadataRecords([METADATA_REC_1, METADATA_REC_4]);

    const libraries = await e
      .select(e.metadata.Library, () => ({
        ...e.metadata.Library['*'],
        specimen: {
          internalId: true,
        },
      }))
      .run(edgeDbClient);

    const specimens = await e
      .select(e.metadata.Specimen, () => ({
        ...e.metadata.Specimen['*'],
      }))
      .run(edgeDbClient);

    // Expecting 2 library record belong to the same subject
    expect(specimens.length).toBe(1);
    expect(libraries.length).toBe(2);

    // Checks if both libraries belong to the same subject
    const subjectId = specimens[0].internalId;
    for (const l of libraries) {
      expect(l.specimen?.internalId).toBe(subjectId);
    }
  });

  it('libraries with both the same specimen and subject', async () => {
    await gService.syncGoogleMetadataRecords([METADATA_REC_1, METADATA_REC_4]);

    const specimens = await e
      .select(e.metadata.Specimen, () => ({
        ...e.metadata.Specimen['*'],
        subject: { internalId: true },
      }))
      .run(edgeDbClient);

    const subjects = await e
      .select(e.metadata.Subject, () => ({ ...e.metadata.Subject['*'] }))
      .run(edgeDbClient);

    expect(subjects.length).toBe(1);
    expect(specimens.length).toBe(1);

    expect(specimens[0].subject?.internalId).toBe(subjects[0].internalId);
  });

  it('test insert and update works', async () => {
    await gService.syncGoogleMetadataRecords(METADATA_GOOGLE_OBJ);

    const libraries = await e
      .select(e.metadata.Library, () => ({ ...e.metadata.Library['*'] }))
      .run(edgeDbClient);

    const specimens = await e
      .select(e.metadata.Specimen, () => ({ ...e.metadata.Specimen['*'] }))
      .run(edgeDbClient);

    const subjects = await e
      .select(e.metadata.Subject, () => ({ ...e.metadata.Subject['*'] }))
      .run(edgeDbClient);

    // Testing for all google object exist in Db
    for (const m of METADATA_GOOGLE_OBJ) {
      expect(libraries.find((l) => l.internalId == m.LibraryID));
      expect(specimens.find((s) => s.internalId == m.SampleID));
      expect(subjects.find((s) => s.internalId == m.SubjectID));
    }
  });
});
