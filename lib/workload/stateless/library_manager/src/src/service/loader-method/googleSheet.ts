import { Client } from 'edgedb';
import { ulid } from 'ulid';
import { metadata } from '../../../dbschema/interfaces';
import { isEqual } from 'lodash';
import { inject, injectable } from 'tsyringe';
import { Logger } from 'pino';
import { JWT } from 'google-auth-library';
import { GetParameterCommand, SSMClient } from '@aws-sdk/client-ssm';
import { GoogleSpreadsheet } from 'google-spreadsheet';
import {
  selectLibraryByIdQuery,
  selectSpecimenByIdQuery,
  selectSubjectByIdQuery,
} from '../../../dbschema/queries';
import {
  hasSubjectRecordChange,
  insertSubjectRecord,
  updateSubjectRecord,
} from '../helpers/metadata/subject-helper';
import { systemAuditEventPattern } from '../helpers/audit-helper';
import { Transaction } from 'edgedb/dist/transaction';
import {
  insertSpecimenRecord,
  isSpecimenPropsChange,
  updateSpecimenRecord,
} from '../helpers/metadata/specimen-helper';
import {
  LibraryType,
  insertLibraryRecord,
  isLibraryRecordNeedUpdate,
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
    const rows = await sheet.getRows();

    return rows.map(
      (row) => <Record<GoogleMetadataTrackingHeader, string | undefined>>row.toObject()
    );
  }

  protected async syncSubject(props: { internalId: string; externalId: string | null }) {
    const subject = await selectSubjectByIdQuery(this.edgeDbClient, {
      internalId: props.internalId,
    });

    // If subject does not exist => insert one
    if (!subject) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new subject record: ${props.internalId}`,
        async (tx: Transaction) => {
          const r = await insertSubjectRecord(tx, {
            orcaBusId: `sbj.${ulid()}`,
            internalId: props.internalId,
            externalId: props.externalId,
          });
          return r;
        }
      );
    }

    // Check if there it is the same with what we had in record and update if not
    if (hasSubjectRecordChange(subject, props)) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing subject record: ${props.internalId}`,
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

  protected async syncSpecimen(props: {
    internalId: string;
    externalId: string | null;
    subjectOrcaBusId?: string;
    source: string | null;
  }) {
    const specimen = await selectSpecimenByIdQuery(this.edgeDbClient, {
      internalId: props.internalId,
    });

    // If subject does not exist => insert one
    if (!specimen) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new specimen record: ${props.internalId}`,
        async (tx: Transaction) => {
          const r = await insertSpecimenRecord(tx, {
            orcaBusId: `spc.${ulid()}`,
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
      isSpecimenPropsChange(
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
        `Update existing specimen record: ${props.internalId}`,
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

  protected async syncLibrary(props: {
    internalId: string;
    phenotype: metadata.Phenotype | null;
    workflow: metadata.WorkflowTypes | null;
    quality: metadata.Quality | null;
    type: metadata.LibraryTypes | null;
    assay: string | null;
    coverage: string | null;
    specimenId?: string;
  }) {
    const library = await selectLibraryByIdQuery(this.edgeDbClient, {
      libraryId: props.internalId,
    });
    // If library does not exist => insert one
    if (!library) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new library record: ${props.internalId}`,
        async (tx: Transaction) => {
          const r = await insertLibraryRecord(tx, {
            orcaBusId: `lib.${ulid()}`,
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
    if (isLibraryRecordNeedUpdate(library, props)) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing specimen record: ${props.internalId}`,
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

  public async syncGoogleMetadataRecords(
    sheetRecords: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ) {
    for (const rec of sheetRecords) {
      // Sync subject
      const subject = rec.SubjectID
        ? await this.syncSubject({
            internalId: rec.SubjectID,
            externalId: rec.ExternalSubjectID ?? null,
          })
        : undefined;

      // Sync Sample
      const sample = rec.SampleID
        ? await this.syncSpecimen({
            internalId: rec.SampleID,
            externalId: rec.ExternalSampleID ?? null,
            subjectOrcaBusId: subject?.orcaBusId,
            source: rec.Source ?? null,
          })
        : undefined;

      // Sync Library
      if (rec.LibraryID) {
        await this.syncLibrary({
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

  // async downloadGoogleSpreadsheet() {}
}
// What if a person is half filling and value not completed yet?
