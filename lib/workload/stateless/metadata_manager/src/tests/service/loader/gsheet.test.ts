import { registerTypes } from '../test-dependency.common';
import { MetadataGoogleService } from '../../../src/service/loader-method/googleSheet';
import { METADATA_GOOGLE_REC_1 } from './gsheet.common';
import { isEqual } from 'lodash';

const testContainer = registerTypes();
let gService: MetadataGoogleService;

describe('metadata record from GoogleSheet tests', () => {
  beforeAll(async () => {
    gService = testContainer.resolve(MetadataGoogleService);
  });

  it('google record converted to internal types', async () => {
    const convertedResultArr = gService.convertToMetadataRecord([METADATA_GOOGLE_REC_1]);

    expect(convertedResultArr.length).toBe(1);
    expect(
      isEqual(convertedResultArr[0], {
        subject: { internalId: 'SUBIDA', externalId: 'EXTSUBIDA' },
        specimen: { internalId: 'SAMIDA', externalId: null, source: 'FFPE' },
        library: {
          internalId: 'LIB01',
          phenotype: null,
          workflow: 'clinical',
          quality: null,
          type: 'WTS',
          assay: 'NebRNA',
          coverage: '6.0',
        },
      })
    ).toBe(true);
  });
});
