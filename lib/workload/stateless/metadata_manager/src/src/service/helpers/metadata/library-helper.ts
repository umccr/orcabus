import { insertLibraryQuery, updateLibraryQuery } from '../../../../dbschema/queries';
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
  specimenOrcaBusId?: string;
};

export const isLibraryIdentical = (
  dbValue: Partial<LibraryType>,
  newValue: Partial<LibraryType>
) => {
  const old = {
    inId: dbValue.internalId,
    exId: dbValue.externalId,
    phenotype: dbValue.phenotype,
    workflow: dbValue.workflow,
    quality: dbValue.quality,
    type: dbValue.type,
    assay: dbValue.assay,
    coverage: dbValue.coverage,
    specimenOrcaBusId: dbValue.specimenOrcaBusId,
  };
  const new_ = {
    inId: newValue.internalId,
    exId: newValue.externalId,
    phenotype: newValue.phenotype,
    workflow: newValue.workflow,
    quality: newValue.quality,
    type: newValue.type,
    assay: newValue.assay,
    coverage: newValue.coverage,
    specimenOrcaBusId: newValue.specimenOrcaBusId,
  };

  return !isEqual(old, new_);
};

export const insertLibraryRecord = async (tx: Transaction, props: LibraryType) => {
  await insertLibraryQuery(tx, {
    orcaBusId: props.orcaBusId,
    internalId: props.internalId,
    phenotype: props.phenotype,
    workflow: props.workflow,
    quality: props.quality,
    type: props.type,
    assay: props.assay,
    coverage: props.coverage,
    specimenOrcaBusId: props.specimenOrcaBusId,
  });

  return props;
};

export const updateLibraryRecord = async (tx: Transaction, props: LibraryType) => {
  await updateLibraryQuery(tx, {
    orcaBusId: props.orcaBusId,
    internalId: props.internalId,
    phenotype: props.phenotype,
    workflow: props.workflow,
    quality: props.quality,
    type: props.type,
    assay: props.assay,
    coverage: props.coverage,
    specimenOrcaBusId: props.specimenOrcaBusId,
  });

  return props;
};
