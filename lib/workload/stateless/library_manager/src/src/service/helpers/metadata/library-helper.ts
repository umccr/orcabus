import { insertLibraryQuery, linkLibraryWithSpecimen } from '../../../../dbschema/queries';
import { Transaction } from 'edgedb/dist/transaction';
import { MetadataIdentifiableType } from './metadata-helper';
import { metadata } from '../../../../dbschema/interfaces';
import { isEqual } from 'lodash';

export type LibraryType = MetadataIdentifiableType & {
  phenotype: metadata.Phenotype | null;
  workflow: metadata.WorkflowTypes | null;
  quality: metadata.Quality | null;
  type: metadata.LibraryTypes | null;
  assay: string | null;
  coverage: string | null;
  specimenId?: string;
};

export const isLibraryRecordNeedUpdate = (dbValue: LibraryType, newValue: LibraryType) => {
  return !isEqual(dbValue, newValue);
};

export const insertLibraryRecord = async (tx: Transaction, props: LibraryType) => {
  await insertLibraryQuery(tx, {
    identifier: props.identifier,
    phenotype: props.phenotype,
    workflow: props.workflow,
    quality: props.quality,
    type: props.type,
    assay: props.assay,
    coverage: props.coverage,
  });

  if (props.specimenId) {
    await linkLibraryWithSpecimen(tx, {
      libraryId: props.identifier,
      specimenId: props.specimenId,
    });
  }
  return props;
};
