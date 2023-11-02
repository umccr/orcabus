// must be first and before any DI is used
import 'reflect-metadata';
import { createDependencyContainer } from '../bootstrap/dependency-injection';

import { MetadataService } from '../service/metadata';
import { MetadataGoogleService } from '../service/loader-method/googleSheet';

export const handler = async () => {
  const dc = await createDependencyContainer();

  const metadataGoogleService = dc.resolve(MetadataGoogleService);
  const metadataService = dc.resolve(MetadataService);

  const downloadedMetadata = await metadataGoogleService.downloadGoogleMetadata();

  const convertedRecord = metadataGoogleService.convertToMetadataRecord(downloadedMetadata);

  // Some syncing
  await metadataService.upsertMetadataRecords(convertedRecord);

  await metadataService.removeDeletedMetadataRecords(convertedRecord);

  return {
    statusCode: 200,
  };
};
