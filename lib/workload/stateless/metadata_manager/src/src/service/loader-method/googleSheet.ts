import { Client } from 'edgedb';
import { ulid } from 'ulid';
import { metadata } from '../../../dbschema/interfaces';
import { inject, injectable } from 'tsyringe';
import { Logger } from 'pino';
import { JWT } from 'google-auth-library';
import { GetParameterCommand, SSMClient } from '@aws-sdk/client-ssm';
import { GoogleSpreadsheet } from 'google-spreadsheet';
import {
  deleteLibraryByOrcaBusId,
  deleteSpecimenByOrcaBusId,
  deleteSubjectByOrcaBusId,
  selectAllLibraryQuery,
  selectAllSpecimenQuery,
  selectAllSubjectQuery,
  selectLibraryByInternalIdQuery,
  selectSpecimenByInternalIdQuery,
  selectSubjectByInternalIdQuery,
} from '../../../dbschema/queries';
import {
  isSubjectIdentical,
  insertSubjectRecord,
  updateSubjectRecord,
} from '../helpers/metadata/subject-helper';
import { systemAuditEventPattern } from '../helpers/audit-helper';
import { Transaction } from 'edgedb/dist/transaction';
import {
  insertSpecimenRecord,
  isSpecimenIdentical,
  updateSpecimenRecord,
} from '../helpers/metadata/specimen-helper';
import {
  insertLibraryRecord,
  isLibraryIdentical,
  updateLibraryRecord,
} from '../helpers/metadata/library-helper';

const GDRIVE_SERVICE_ACCOUNT = '/umccr/google/drive/lims_service_account_json';
const TRACKING_SHEET_ID = '/umccr/google/drive/tracking_sheet_id';
// const LIMS_SHEET_ID = '/umccr/google/drive/lims_sheet_id'; // DEPRECATE?

// This will tell from which year the system should query the worksheet
// Note: The title of the sheet are supposed to be th year
const YEAR_START = 2017;

type GoogleMetadataTrackingHeader =
  | 'LibraryID'
  | 'SampleID'
  | 'ExternalSampleID'
  | 'SubjectID'
  | 'ExternalSubjectID'
  | 'Phenotype'
  | 'Quality'
  | 'Source'
  | 'ProjectOwner'
  | 'ProjectName'
  | 'ExperimentID'
  | 'Type'
  | 'Assay'
  | 'Workflow'
  | 'Coverage (X)';

@injectable()
export class MetadataGoogleService {
  constructor(
    @inject('Database') private readonly edgeDbClient: Client,
    @inject('Settings') private readonly settings: Record<string, string>,
    @inject('Logger') private readonly logger: Logger,
    @inject('SSMClient') private readonly ssmClient: SSMClient
  ) {}

  private async getParameterValue(parameterString: string) {
    const input = {
      Name: parameterString,
      WithDecryption: true,
    };
    const command = new GetParameterCommand(input);
    return (await this.ssmClient.send(command)).Parameter?.Value;
  }

  /**
   * Get SpreadSheet values from Google Drive
   * @param sheetTitle
   * @returns
   */
  public async getSheetObject(
    sheetTitle: string
  ): Promise<Record<GoogleMetadataTrackingHeader, string | undefined>[]> {
    const googleAuthString = await this.getParameterValue(GDRIVE_SERVICE_ACCOUNT);
    if (!googleAuthString) throw new Error('No GDrive credential found!');

    const googleSheetId = await this.getParameterValue(TRACKING_SHEET_ID);
    if (!googleSheetId) throw new Error('No Google Sheet Id found!');

    const googleAuthJson = JSON.parse(googleAuthString);
    const jwt = new JWT({
      email: googleAuthJson.client_email,
      key: googleAuthJson.private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });

    const doc = new GoogleSpreadsheet(googleSheetId, jwt);
    await doc.loadInfo();

    const sheet = doc.sheetsByTitle[sheetTitle];
    if (!sheet) throw new Error(`No sheet found with title: ${sheetTitle}`);

    const rows = await sheet.getRows();
    return rows.map(
      (row) => <Record<GoogleMetadataTrackingHeader, string | undefined>>row.toObject()
    );
  }

  /**
   * Insert or Update for the subject specified in the properties
   * @param props
   * @returns
   */
  protected async upsertSubject(props: { internalId: string; externalId: string | null }) {
    const subject = await selectSubjectByInternalIdQuery(this.edgeDbClient, {
      internalId: props.internalId,
    });

    // If subject does not exist => insert one
    if (!subject) {
      const assignedOrcaBusId = `sbj.${ulid()}`;
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new subject record: ${assignedOrcaBusId}`,
        async (tx: Transaction) => {
          const r = await insertSubjectRecord(tx, {
            orcaBusId: assignedOrcaBusId,
            internalId: props.internalId,
            externalId: props.externalId,
          });
          return r;
        }
      );
    }

    // Check if there it is the same with what we had in record and update if not
    if (isSubjectIdentical(subject, props)) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing subject record: ${subject.orcaBusId}`,
        async (tx: Transaction) => {
          const r = await updateSubjectRecord(tx, {
            orcaBusId: subject.orcaBusId,
            internalId: props.internalId,
            externalId: props.externalId,
          });
          return r;
        }
      );
    }
    return subject;
  }

  /**
   * Check the current records and deletes it if no longer exist in source data
   * @param sourceData The source truth of data
   * @returns
   */
  protected async checkAndRemoveSubject(
    sourceData: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ) {
    const allExistingSubject = await selectAllSubjectQuery(this.edgeDbClient);
    for (const s of allExistingSubject) {
      const isExist = !!sourceData.find((source) => source.SubjectID == s.internalId);

      if (!isExist) {
        return systemAuditEventPattern(
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
  protected async upsertSpecimen(props: {
    internalId: string;
    externalId: string | null;
    subjectOrcaBusId?: string;
    source: string | null;
  }) {
    const specimen = await selectSpecimenByInternalIdQuery(this.edgeDbClient, {
      internalId: props.internalId,
    });

    // If subject does not exist => insert one
    if (!specimen) {
      const assignedOrcaBusId = `spc.${ulid()}`;

      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new specimen record: ${assignedOrcaBusId}`,
        async (tx: Transaction) => {
          const r = await insertSpecimenRecord(tx, {
            orcaBusId: assignedOrcaBusId,
            internalId: props.internalId,
            externalId: props.externalId,
            subjectOrcaBusId: props.subjectOrcaBusId,
            source: props.source,
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
      return systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing specimen record: ${specimen.orcaBusId}`,
        async (tx: Transaction) => {
          const r = await updateSpecimenRecord(tx, {
            orcaBusId: specimen.orcaBusId,
            internalId: props.internalId,
            externalId: props.externalId,
            source: props.source,
            subjectOrcaBusId: props.subjectOrcaBusId,
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
  protected async checkAndRemoveSpecimen(
    sourceData: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ) {
    const allExistingSpc = await selectAllSpecimenQuery(this.edgeDbClient);
    for (const s of allExistingSpc) {
      const isExist = !!sourceData.find((source) => source.SampleID == s.internalId);

      if (!isExist) {
        return systemAuditEventPattern(
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
  protected async upsertLibrary(props: {
    internalId: string;
    phenotype: metadata.Phenotype | null;
    workflow: metadata.WorkflowTypes | null;
    quality: metadata.Quality | null;
    type: metadata.LibraryTypes | null;
    assay: string | null;
    coverage: string | null;
    specimenId?: string;
  }) {
    const library = await selectLibraryByInternalIdQuery(this.edgeDbClient, {
      libraryId: props.internalId,
    });
    // If library does not exist => insert one
    if (!library) {
      const assignedOrcaBusId = `lib.${ulid()}`;
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new library record: ${assignedOrcaBusId}`,
        async (tx: Transaction) => {
          const r = await insertLibraryRecord(tx, {
            orcaBusId: assignedOrcaBusId,
            internalId: props.internalId,
            phenotype: props.phenotype,
            workflow: props.workflow,
            quality: props.quality,
            type: props.type,
            assay: props.assay,
            coverage: props.coverage,
            specimenOrcaBusId: props.specimenId,
          });
          return r;
        }
      );
    }

    // Check if specimen is the same with what we had in record and update if not
    if (isLibraryIdentical(library, props)) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing specimen record: ${library.orcaBusId}`,
        async (tx: Transaction) => {
          const r = await updateLibraryRecord(tx, {
            orcaBusId: library.orcaBusId,
            internalId: props.internalId,
            phenotype: props.phenotype,
            workflow: props.workflow,
            quality: props.quality,
            type: props.type,
            assay: props.assay,
            coverage: props.coverage,
            specimenOrcaBusId: props.specimenId,
          });
          return r;
        }
      );
    }
    return library;
  }

  /**
   * Check the current records and deletes it if no longer exist in source data
   * @param sourceData The source truth of data
   * @returns
   */
  protected async checkAndRemoveLibrary(
    sourceData: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ) {
    const allExistingLib = await selectAllLibraryQuery(this.edgeDbClient);
    for (const s of allExistingLib) {
      const isExist = !!sourceData.find((source) => source.LibraryID == s.internalId);

      if (!isExist) {
        return systemAuditEventPattern(
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
   * Update or Insert record based on the existing google metadata records
   * @param sheetRecords
   */
  public async upsertGoogleMetadataRecords(
    sheetRecords: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ) {
    for (const rec of sheetRecords) {
      // Sync subject
      const subject = rec.SubjectID
        ? await this.upsertSubject({
            internalId: rec.SubjectID,
            externalId: rec.ExternalSubjectID ?? null,
          })
        : undefined;

      // Sync Sample
      const sample = rec.SampleID
        ? await this.upsertSpecimen({
            internalId: rec.SampleID,
            externalId: rec.ExternalSampleID ?? null,
            subjectOrcaBusId: subject?.orcaBusId,
            source: rec.Source ?? null,
          })
        : undefined;

      // Sync Library
      if (rec.LibraryID) {
        await this.upsertLibrary({
          internalId: rec.LibraryID,
          phenotype: <metadata.Phenotype>rec.Phenotype ? <metadata.Phenotype>rec.Phenotype : null,
          workflow: <metadata.WorkflowTypes>rec.Workflow
            ? <metadata.WorkflowTypes>rec.Workflow
            : null,
          quality: <metadata.Quality>rec.Quality ? <metadata.Quality>rec.Quality : null,
          type: <metadata.LibraryTypes>rec.Type ? <metadata.LibraryTypes>rec.Type : null,
          assay: rec.Assay ? rec.Assay : null,
          coverage: rec['Coverage (X)'] ? rec['Coverage (X)'] : null,
          specimenId: sample?.orcaBusId,
        });
      }
    }
  }

  /**
   * Check and delete if record no longer exist from external parties across all metadata
   * @param sheetRecords The data that the app relies on
   */
  public async removeDeletedGoogleMetadataRecords(
    sheetRecords: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ) {
    await this.checkAndRemoveSubject(sheetRecords);

    await this.checkAndRemoveSpecimen(sheetRecords);

    await this.checkAndRemoveLibrary(sheetRecords);
  }

  public async downloadGoogleMetadata(): Promise<
    Record<GoogleMetadataTrackingHeader, string | undefined>[]
  > {
    let year = YEAR_START;
    let allRecords: Record<GoogleMetadataTrackingHeader, string | undefined>[] = [];

    // eslint-disable-next-line no-constant-condition
    while (true) {
      try {
        const yearlyMetadataObject = await this.getSheetObject(year.toString());
        allRecords = [...allRecords, ...yearlyMetadataObject];
        year += 1;
      } catch (error) {
        break;
      }
    }

    return allRecords;
  }
}
