import { insertSubjectQuery, updateSubjectQuery } from '../../../../dbschema/queries';
import { Transaction } from 'edgedb/dist/transaction';
import { MetadataIdentifiableType } from './metadata-helper';
import { isEqual } from 'lodash';

export type SubjectType = MetadataIdentifiableType;

export const isSubjectIdentical = (dbValue: SubjectType, newValue: Partial<SubjectType>) => {
  const old = {
    exId: dbValue.externalId,
    inId: dbValue.internalId,
  };
  const new_ = {
    exId: newValue.externalId,
    inId: newValue.internalId,
  };
  return !isEqual(old, new_);
};

export const insertSubjectRecord = async (tx: Transaction, props: SubjectType) => {
  return await insertSubjectQuery(tx, {
    orcaBusId: props.orcaBusId,
    internalId: props.internalId,
    externalId: props.externalId,
  });
};
export const updateSubjectRecord = async (tx: Transaction, props: SubjectType) => {
  return await updateSubjectQuery(tx, {
    orcaBusId: props.orcaBusId,
    internalId: props.internalId,
    externalId: props.externalId,
  });
};
