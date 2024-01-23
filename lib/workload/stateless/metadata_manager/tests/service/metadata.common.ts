import { MetadataRecords } from '../../src/service/metadata';

export const METADATA_REC_1: MetadataRecords = {
  subject: { internalId: 'SUBIDA', externalId: 'EXTSUBIDA' },
  specimen: { internalId: 'SAMIDA', externalId: '', source: 'FFPE' },
  library: {
    internalId: 'LIB01',
    phenotype: null,
    workflow: 'clinical',
    quality: null,
    type: 'WTS',
    assay: 'NebRNA',
    coverage: '6.0',
  },
};

export const METADATA_REC_2: MetadataRecords = {
  subject: { internalId: 'SUBIDB', externalId: 'EXTSUBIDB' },
  specimen: { internalId: 'SAMIDB', externalId: 'EXTSAMB', source: 'FFPE' },
  library: {
    internalId: 'LIB02',
    phenotype: 'tumor',
    workflow: 'clinical',
    quality: 'poor',
    type: 'WTS',
    assay: 'NebRNA',
    coverage: '6.3',
  },
};

export const METADATA_REC_3: MetadataRecords = {
  subject: { internalId: 'SUBIDB', externalId: 'EXTSUBIDB' },
  specimen: { internalId: 'SAMIDB', externalId: 'EXTSAMB', source: 'FFPE' },
  library: {
    internalId: 'LIB03',
    phenotype: 'tumor',
    workflow: 'clinical',
    quality: 'poor',
    type: 'WTS',
    assay: 'NebRNA',
    coverage: '6.0',
  },
};

export const METADATA_REC_4: MetadataRecords = {
  subject: { internalId: 'SUBIDA', externalId: 'EXTSUBIDA' },
  specimen: { internalId: 'SAMIDA', externalId: 'EXTSAMA', source: 'FFPE' },
  library: {
    internalId: 'LIB04',
    phenotype: 'tumor',
    workflow: 'clinical',
    quality: 'poor',
    type: 'WTS',
    assay: 'NebRNA',
    coverage: '6.0',
  },
};

export const METADATA_REC_ARR = [METADATA_REC_1, METADATA_REC_2, METADATA_REC_3, METADATA_REC_4];
