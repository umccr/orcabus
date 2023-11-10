// must be first and before any DI is used
import 'reflect-metadata';
import { createDependencyContainer } from '../bootstrap/dependency-injection';

import { MetadataService } from '../service/metadata';
import { MetadataGoogleService } from '../service/loader-method/googleSheet';
import insertScenario1 from '../test-data/scenario-1';

export const handler = async () => {
  const dc = await createDependencyContainer();

  if (process.env.NODE_ENV === 'development') {
    await insertScenario1(dc);
  } else {
    const metadataGoogleService = dc.resolve(MetadataGoogleService);
    const metadataService = dc.resolve(MetadataService);

    const downloadedMetadata = await metadataGoogleService.downloadGoogleMetadata();
    const convertedRecord = metadataGoogleService.convertToMetadataRecord(downloadedMetadata);

    // Updating Db
    await metadataService.upsertMetadataRecords(convertedRecord);
    await metadataService.removeDeletedMetadataRecords(convertedRecord);
  }

  return {
    statusCode: 200,
  };
};
