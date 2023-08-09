import { insertLibraryQuery } from '../../../../dbschema/queries';
import { Transaction } from 'edgedb/dist/transaction';
import { MetadataIdentifiableType } from './metadata-helper';
import { isEqual } from 'lodash';
import { metadata } from '../../../../dbschema/interfaces';

export type LibraryType = MetadataIdentifiableType & {
  phenotype: metadata.Phenotype | null;
  workflow: metadata.WorkflowTypes | null;
  quality: metadata.Quality | null;
  type: metadata.LibraryTypes | null;
  assay: string | null;
  coverage: number | null;
};

export const insertLibraryRecord = async (tx: Transaction, props: LibraryType) => {
  await insertLibraryQuery(tx, {
    ...props,
  });
  // if (props.subjectId) {
  //   await linkSpecimenWithSubject(tx, {
  //     subjectId: props.subjectId,
  //     specimenId: props.identifier,
  //   });
  // }
  return props;
};
