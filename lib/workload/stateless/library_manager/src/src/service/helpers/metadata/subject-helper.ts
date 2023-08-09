import { insertSubjectQuery, updateSubjectQuery } from '../../../../dbschema/queries';
import { Transaction } from 'edgedb/dist/transaction';
import { MetadataIdentifiableType } from './metadata-helper';

export type SubjectType = MetadataIdentifiableType;

export const insertSubjectRecord = async (tx: Transaction, props: SubjectType) => {
  return await insertSubjectQuery(tx, {
    subjectId: props.identifier,
    externalIdentifiers: props.externalIdentifiers,
  });
};
export const updateSubjectRecord = async (tx: Transaction, props: SubjectType) => {
  return await updateSubjectQuery(tx, {
    subjectId: props.identifier,
    externalIdentifiers: props.externalIdentifiers,
  });
};
