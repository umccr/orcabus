import {
  insertSpecimenQuery,
  linkSpecimenWithSubject,
  updateSpecimenQuery,
} from '../../../../dbschema/queries';
import { Transaction } from 'edgedb/dist/transaction';
import { MetadataIdentifiableType } from './metadata-helper';
import { isEqual } from 'lodash';

export type SpecimenType = MetadataIdentifiableType & {
  subjectId?: string | null;
  source: string | null;
};

export const isSpecimenPropsChange = (dbValue: SpecimenType, newValue: SpecimenType) => {
  const old = {
    exId: dbValue.externalIdentifiers,
    source: dbValue.source,
  };
  const new_ = {
    exId: newValue.externalIdentifiers,
    source: newValue.source,
  };

  return !isEqual(old, new_);
};

// export const isSpecimenSubjectLinkChange = () => {libraryId};

export const insertSpecimenRecord = async (tx: Transaction, props: SpecimenType) => {
  await insertSpecimenQuery(tx, {
    specimenId: props.identifier,
    externalIdentifiers: props.externalIdentifiers,
    source: props.source,
  });
  if (props.subjectId) {
    await linkSpecimenWithSubject(tx, {
      subjectId: props.subjectId,
      specimenId: props.identifier,
    });
  }
  return props;
};
export const updateSpecimenRecord = async (tx: Transaction, props: SpecimenType) => {
  // TODO: Concern could raise to update linked that has been link previously
  await updateSpecimenQuery(tx, {
    specimenId: props.identifier,
    externalIdentifiers: props.externalIdentifiers,
    source: props.source,
  });
  if (props.subjectId) {
    await linkSpecimenWithSubject(tx, {
      subjectId: props.subjectId,
      specimenId: props.identifier,
    });
  }
  return props;
};
