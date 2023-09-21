import e from '../../dbschema/edgeql-js';
import { registerTypes } from './test-dependency.common';
import { METADATA_REC_1, METADATA_REC_4, METADATA_REC_ARR } from './metadata.common';
import { Client } from 'edgedb';
import { resetDb } from './utils';
import { MetadataService } from '../../src/service/metadata';

const testContainer = registerTypes();
let edgeDbClient: Client;
let metadataService: MetadataService;

describe('metadata service test', () => {
  beforeAll(async () => {
    edgeDbClient = testContainer.resolve('Database');
    metadataService = testContainer.resolve(MetadataService);
  });

  beforeEach(async () => {
    await resetDb(edgeDbClient);
  });

  it('two libraries with the same specimen and subject', async () => {
    await metadataService.upsertMetadataRecords([METADATA_REC_1, METADATA_REC_4]);

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
        subject: { internalId: true },
      }))
      .run(edgeDbClient);

    const subjects = await e
      .select(e.metadata.Subject, () => ({ ...e.metadata.Subject['*'] }))
      .run(edgeDbClient);

    // Expecting 2 library record belong to the same subject and specimen
    expect(libraries.length).toBe(2);
    expect(subjects.length).toBe(1);
    expect(specimens.length).toBe(1);

    // Checks if both libraries belong to the same subject
    const specimenId = specimens[0].internalId;
    for (const l of libraries) {
      expect(l.specimen?.internalId).toBe(specimenId);
    }

    // Check if specimen belong to the same subject
    const subjectId = subjects[0].internalId;
    expect(specimens[0].subject?.internalId).toBe(subjectId);
  });

  it('upsert function works as expected and appear in database', async () => {
    await metadataService.upsertMetadataRecords(METADATA_REC_ARR);

    const libraries = await e
      .select(e.metadata.Library, () => ({ ...e.metadata.Library['*'] }))
      .run(edgeDbClient);

    const specimens = await e
      .select(e.metadata.Specimen, () => ({ ...e.metadata.Specimen['*'] }))
      .run(edgeDbClient);

    const subjects = await e
      .select(e.metadata.Subject, () => ({ ...e.metadata.Subject['*'] }))
      .run(edgeDbClient);

    // Testing for all record exist in database
    for (const m of METADATA_REC_ARR) {
      expect(libraries.find((l) => l.internalId == m.library?.internalId));
      expect(specimens.find((s) => s.internalId == m.specimen?.externalId));
      expect(subjects.find((s) => s.internalId == m.subject?.externalId));
    }
  });

  it('destroy all records works as expected', async () => {
    await metadataService.upsertMetadataRecords(METADATA_REC_ARR);

    await metadataService.removeDeletedMetadataRecords([]);

    const libraries = await e
      .select(e.metadata.Library, () => ({ ...e.metadata.Library['*'] }))
      .run(edgeDbClient);

    const specimens = await e
      .select(e.metadata.Specimen, () => ({ ...e.metadata.Specimen['*'] }))
      .run(edgeDbClient);

    const subjects = await e
      .select(e.metadata.Subject, () => ({ ...e.metadata.Subject['*'] }))
      .run(edgeDbClient);

    expect(libraries.length).toBe(0);
    expect(specimens.length).toBe(0);
    expect(subjects.length).toBe(0);
  });

  it('destroy all records works as expected', async () => {
    await metadataService.upsertMetadataRecords(METADATA_REC_ARR);

    await metadataService.removeDeletedMetadataRecords([]);

    const libraries = await e
      .select(e.metadata.Library, () => ({ ...e.metadata.Library['*'] }))
      .run(edgeDbClient);

    const specimens = await e
      .select(e.metadata.Specimen, () => ({ ...e.metadata.Specimen['*'] }))
      .run(edgeDbClient);

    const subjects = await e
      .select(e.metadata.Subject, () => ({ ...e.metadata.Subject['*'] }))
      .run(edgeDbClient);

    expect(libraries.length).toBe(0);
    expect(specimens.length).toBe(0);
    expect(subjects.length).toBe(0);
  });

  it('removing a library that has the same subject and specimen id', async () => {
    await metadataService.upsertMetadataRecords([METADATA_REC_1, METADATA_REC_4]);

    await metadataService.removeDeletedMetadataRecords([METADATA_REC_1]);

    const libraries = await e
      .select(e.metadata.Library, () => ({ ...e.metadata.Library['*'] }))
      .run(edgeDbClient);

    const specimens = await e
      .select(e.metadata.Specimen, () => ({ ...e.metadata.Specimen['*'] }))
      .run(edgeDbClient);

    const subjects = await e
      .select(e.metadata.Subject, () => ({ ...e.metadata.Subject['*'] }))
      .run(edgeDbClient);

    expect(libraries.length).toBe(1);
    expect(specimens.length).toBe(1);
    expect(subjects.length).toBe(1);

    expect(libraries[0].internalId).toBe(METADATA_REC_1.library?.internalId);
    expect(specimens[0].internalId).toBe(METADATA_REC_1.specimen?.internalId);
    expect(subjects[0].internalId).toBe(METADATA_REC_1.subject?.internalId);
  });
});
