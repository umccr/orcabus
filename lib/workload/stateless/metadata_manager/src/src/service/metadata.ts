import { Client } from 'edgedb';
import { injectable, inject } from 'tsyringe';
import {
  isSubjectIdentical,
  insertSubjectRecord,
  updateSubjectRecord,
  SubjectType,
} from './helpers/metadata/subject-helper';
import { ulid } from 'ulid';
import {
  SpecimenType,
  insertSpecimenRecord,
  isSpecimenIdentical,
  updateSpecimenRecord,
} from './helpers/metadata/specimen-helper';
import {
  LibraryType,
  insertLibraryRecord,
  isLibraryIdentical,
  updateLibraryRecord,
} from './helpers/metadata/library-helper';
import {
  SelectAllLibraryQueryArgs,
  SelectAllSubjectQueryArgs,
  deleteLibraryByOrcaBusId,
  deleteSpecimenByOrcaBusId,
  deleteSubjectByOrcaBusId,
  selectAllLibraryQuery,
  selectAllSpecimenQuery,
  selectAllSubjectQuery,
  selectLibraryByInternalIdQuery,
  selectSpecimenByInternalIdQuery,
  selectSubjectByInternalIdQuery,
} from '../../dbschema/queries';
import { Transaction } from 'edgedb/dist/transaction';
import { systemAuditEventPattern } from './helpers/audit-helper';
import { Logger } from 'pino';

export type MetadataRecords = {
  subject?: Omit<SubjectType, 'orcaBusId'>;
  specimen?: Omit<SpecimenType, 'orcaBusId'>;
  library?: Omit<LibraryType, 'orcaBusId'>;
};

@injectable()
export class MetadataService {
  constructor(
    @inject('Database') private readonly edgeDbClient: Client,
    @inject('Logger') private readonly logger: Logger
  ) {}

  /**
   * Update or Insert for the subject specified in the properties
   * @param props
   * @returns
   */
  protected async upsertSubject(props: Omit<SubjectType, 'orcaBusId'>) {
    const subject = await selectSubjectByInternalIdQuery(this.edgeDbClient, {
      internalId: props.internalId,
    });

    // If subject does not exist => insert one
    if (!subject) {
      const assignedOrcaBusId = `sbj.${ulid()}`;
      return await systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new subject record: ${assignedOrcaBusId}`,
        async (tx: Transaction) => {
          const r = await insertSubjectRecord(tx, {
            ...props,
            orcaBusId: assignedOrcaBusId,
          });
          return r;
        }
      );
    }

    // Check if there it is the same with what we had in record and update if not
    if (isSubjectIdentical(subject, props)) {
      return await systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing subject record: ${subject.orcaBusId}`,
        async (tx: Transaction) => {
          const r = await updateSubjectRecord(tx, {
            ...props,
            orcaBusId: subject.orcaBusId,
          });
          return r;
        }
      );
    }
    return subject;
  }

  /**
   * Check the current records and deletes it if no longer exist in the source truth of data
   * @param sourceData The source truth of data
   * @returns
   */
  protected async checkAndRemoveSubject(sourceInternalIdArray: string[]) {
    const allExistingSubject = await selectAllSubjectQuery(this.edgeDbClient, {});
    for (const s of allExistingSubject.results) {
      const shouldRetain = !!sourceInternalIdArray.find(
        (sourceInternalId) => sourceInternalId == s.internalId
      );

      if (!shouldRetain) {
        await systemAuditEventPattern(
          this.edgeDbClient,
          'D',
          `Delete subject record: ${s.orcaBusId}`,
          async (tx: Transaction) => {
            const r = await deleteSubjectByOrcaBusId(tx, {
              orcaBusId: s.orcaBusId,
            });
            return r;
          }
        );
      }
    }
  }

  /**
   * Insert or Update for the specimen specified in the properties
   * @param props
   * @returns
   */
  protected async upsertSpecimen(
    props: Omit<SpecimenType, 'orcaBusId'> & {
      subjectOrcaBusId?: string;
    }
  ) {
    const specimen = await selectSpecimenByInternalIdQuery(this.edgeDbClient, {
      internalId: props.internalId,
    });

    // If subject does not exist => insert one
    if (!specimen) {
      const assignedOrcaBusId = `spc.${ulid()}`;

      return await systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new specimen record: ${assignedOrcaBusId}`,
        async (tx: Transaction) => {
          const r = await insertSpecimenRecord(tx, {
            ...props,
            orcaBusId: assignedOrcaBusId,
          });
          return r;
        }
      );
    }

    // Check if specimen is the same with what we had in record and update if not
    if (
      isSpecimenIdentical(
        {
          internalId: specimen.internalId,
          externalId: specimen.externalId,
          source: specimen.source,
          subjectOrcaBusId: specimen.subjectId,
        },
        { ...props }
      )
    ) {
      return await systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing specimen record: ${specimen.orcaBusId}`,
        async (tx: Transaction) => {
          const r = await updateSpecimenRecord(tx, {
            ...props,
            orcaBusId: specimen.orcaBusId,
          });
          return r;
        }
      );
    }
    return specimen;
  }

  /**
   * Check the current records and deletes it if no longer exist in source data
   * @param sourceData The source truth of data
   * @returns
   */
  protected async checkAndRemoveSpecimen(sourceInternalIdArray: string[]) {
    const allExistingSpc = await selectAllSpecimenQuery(this.edgeDbClient, {});
    for (const s of allExistingSpc.results) {
      const shouldRetain = !!sourceInternalIdArray.find(
        (sourceInternalId) => sourceInternalId == s.internalId
      );

      if (!shouldRetain) {
        await systemAuditEventPattern(
          this.edgeDbClient,
          'D',
          `Delete specimen record: ${s.orcaBusId}`,
          async (tx: Transaction) => {
            const r = await deleteSpecimenByOrcaBusId(tx, {
              orcaBusId: s.orcaBusId,
            });
            return r;
          }
        );
      }
    }
  }

  /**
   * Insert or Update for the library specified in the properties
   * @param props
   * @returns
   */
  protected async upsertLibrary(
    props: Omit<LibraryType, 'orcaBusId'> & {
      specimenOrcaBusId?: string;
    }
  ) {
    const library = await selectLibraryByInternalIdQuery(this.edgeDbClient, {
      libraryId: props.internalId,
    });
    // If library does not exist => insert one
    if (!library) {
      const assignedOrcaBusId = `lib.${ulid()}`;
      return await systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new library record: ${assignedOrcaBusId}`,
        async (tx: Transaction) => {
          const r = await insertLibraryRecord(tx, {
            ...props,
            orcaBusId: assignedOrcaBusId,
          });
          return r;
        }
      );
    }

    // Check if specimen is the same with what we had in record and update if not
    if (isLibraryIdentical(library, props)) {
      return await systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing specimen record: ${library.orcaBusId}`,
        async (tx: Transaction) => {
          const r = await updateLibraryRecord(tx, {
            ...props,
            orcaBusId: library.orcaBusId,
          });
          return r;
        }
      );
    }
    return library;
  }

  /**
   * Check the current records and deletes it if no longer exist in source data
   * @param internalIdArray The internalIds in an array of the truth
   * @returns
   */
  protected async checkAndRemoveLibrary(sourceInternalIdArray: string[]) {
    const allExistingLib = await selectAllLibraryQuery(this.edgeDbClient, {});
    for (const s of allExistingLib.results) {
      const shouldRetain = !!sourceInternalIdArray.find(
        (sourceInternalId) => sourceInternalId == s.internalId
      );

      if (!shouldRetain) {
        await systemAuditEventPattern(
          this.edgeDbClient,
          'D',
          `Delete library record: ${s.orcaBusId}`,
          async (tx: Transaction) => {
            const r = await deleteLibraryByOrcaBusId(tx, {
              orcaBusId: s.orcaBusId,
            });
            return r;
          }
        );
      }
    }
  }

  /**
   * Update or Insert record based on the given (source of truth) data
   * @param metadataRecords
   */
  public async upsertMetadataRecords(metadataRecords: MetadataRecords[]) {
    this.logger.info(`Upsert for any new record that doesn't match or exist within the record`);

    for (const rec of metadataRecords) {
      // Subject
      const subject = rec.subject ? await this.upsertSubject(rec.subject) : undefined;

      // Specimen
      const sample = rec.specimen
        ? await this.upsertSpecimen({
            ...rec.specimen,
            subjectOrcaBusId: subject?.orcaBusId,
          })
        : undefined;

      // Library
      if (rec.library) {
        await this.upsertLibrary({
          ...rec.library,
          specimenOrcaBusId: sample?.orcaBusId,
        });
      }
    }
  }

  /**
   * Check and delete if internalId is no longer exist in the single source of truth data
   * @param metadataRecords the source of true data
   */
  public async removeDeletedMetadataRecords(metadataRecords: MetadataRecords[]) {
    this.logger.info('Removing any existing record that does not exist in the current dataset');
    const internalIdArrays: { subject: string[]; specimen: string[]; library: string[] } = {
      subject: [],
      specimen: [],
      library: [],
    };

    for (const r of metadataRecords) {
      if (r.subject?.internalId) {
        internalIdArrays.subject.push(r.subject?.internalId);
      }

      if (r.specimen?.internalId) {
        internalIdArrays.specimen.push(r.specimen?.internalId);
      }

      if (r.library?.internalId) {
        internalIdArrays.library.push(r.library?.internalId);
      }
    }

    await this.checkAndRemoveSubject(internalIdArrays.subject);
    await this.checkAndRemoveSpecimen(internalIdArrays.specimen);
    await this.checkAndRemoveLibrary(internalIdArrays.library);
  }

  public async getAllLibrary(libraryQuery: SelectAllLibraryQueryArgs) {
    return await selectAllLibraryQuery(this.edgeDbClient, libraryQuery);
  }

  public async getAllSpecimen(specimenQuery: SelectAllSubjectQueryArgs) {
    return await selectAllSpecimenQuery(this.edgeDbClient, specimenQuery);
  }

  public async getAllSubject(subjectQuery: SelectAllSubjectQueryArgs) {
    return await selectAllSubjectQuery(this.edgeDbClient, subjectQuery);
  }
}
