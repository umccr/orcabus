import { insertSpecimenQuery, updateSpecimenQuery } from '../../../../dbschema/queries';
import { Transaction } from 'edgedb/dist/transaction';
import { MetadataIdentifiableType } from './metadata-helper';
import { isEqual } from 'lodash';

export type SpecimenType = MetadataIdentifiableType & {
  subjectOrcaBusId?: string | null;
  source: string | null;
};

export const isSpecimenIdentical = (
  dbValue: Partial<SpecimenType>,
  newValue: Partial<SpecimenType>
) => {
  const old = {
    inId: dbValue.internalId,
    exId: dbValue.externalId,
    source: dbValue.source,
    subjectOrcaBusId: dbValue.subjectOrcaBusId,
  };
  const new_ = {
    inId: newValue.internalId,
    exId: newValue.externalId,
    source: newValue.source,
    subjectOrcaBusId: newValue.subjectOrcaBusId,
  };

  return !isEqual(old, new_);
};

export const insertSpecimenRecord = async (tx: Transaction, props: SpecimenType) => {
  return await insertSpecimenQuery(tx, {
    orcaBusId: props.orcaBusId,
    internalId: props.internalId,
    externalId: props.externalId,
    source: props.source,
    subjectOrcaBusId: props.subjectOrcaBusId,
  });
};

export const updateSpecimenRecord = async (tx: Transaction, props: SpecimenType) => {
  return await updateSpecimenQuery(tx, {
    orcaBusId: props.orcaBusId,
    internalId: props.internalId,
    externalId: props.externalId,
    source: props.source,
    subjectOrcaBusId: props.subjectOrcaBusId,
  });
};
