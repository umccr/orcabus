import { Client } from 'edgedb';
import { metadata } from '../../../dbschema/interfaces';
import { isEqual } from 'lodash';
import { inject, injectable } from 'tsyringe';
import { Logger } from 'pino';
import { JWT } from 'google-auth-library';
import { GetParameterCommand, SSMClient } from '@aws-sdk/client-ssm';
import { GoogleSpreadsheet } from 'google-spreadsheet';
import {
  insertLibraryQuery,
  selectLibraryByIdQuery,
  selectSpecimenByIdQuery,
  selectSubjectByIdQuery,
} from '../../../dbschema/queries';
import { insertSubjectRecord, updateSubjectRecord } from '../helpers/metadata/subject-helper';
import { systemAuditEventPattern } from '../helpers/audit-helper';
import { Transaction } from 'edgedb/dist/transaction';
import {
  insertSpecimenRecord,
  isSpecimenPropsNeedUpdate,
  updateSpecimenRecord,
} from '../helpers/metadata/specimen-helper';
import { LibraryType, insertLibraryRecord } from '../helpers/metadata/library-helper';

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

  private convertExIdToDbFormat(exId: string | null) {
    return exId ? { externalSubjectId: exId } : undefined;
  }

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

  protected async syncSubject(props: { identifier: string; externalIdentifiers: string | null }) {
    const convertedExId = this.convertExIdToDbFormat(props.externalIdentifiers);

    const subject = await selectSubjectByIdQuery(this.edgeDbClient, {
      subjectId: props.identifier,
    });

    // If subject does not exist => insert one
    if (!subject) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new subject record: ${props.identifier}`,
        async (tx: Transaction) => {
          const r = await insertSubjectRecord(tx, {
            identifier: props.identifier,
            externalIdentifiers: convertedExId,
          });
          return r;
        }
      );
    }

    // Check if there it is the same with what we had in record and update if not
    if (!isEqual(convertedExId, subject.externalIdentifiers)) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing subject record: ${props.identifier}`,
        async (tx: Transaction) => {
          const r = await updateSubjectRecord(tx, {
            identifier: props.identifier,
            externalIdentifiers: convertedExId,
          });
          return r;
        }
      );
    }
  }

  protected async syncSpecimen(props: {
    identifier: string;
    externalIdentifiers: string | null;
    subjectId: string | null;
    source: string | null;
  }) {
    const convertedExId = this.convertExIdToDbFormat(props.externalIdentifiers);
    const specimen = await selectSpecimenByIdQuery(this.edgeDbClient, {
      specimenId: props.identifier,
    });
    // If subject does not exist => insert one
    if (!specimen) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new specimen record: ${props.identifier}`,
        async (tx: Transaction) => {
          const r = await insertSpecimenRecord(tx, {
            identifier: props.identifier,
            externalIdentifiers: convertedExId,
            subjectId: props.subjectId,
            source: props.source,
          });
          return r;
        }
      );
    }

    // Check if specimen is the same with what we had in record and update if not
    if (
      isSpecimenPropsNeedUpdate(
        {
          identifier: props.identifier,
          externalIdentifiers: <Record<string, string>>specimen.externalIdentifiers,
          source: specimen.source,
        },
        { ...props, externalIdentifiers: convertedExId }
      )
    ) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'U',
        `Update existing specimen record: ${props.identifier}`,
        async (tx: Transaction) => {
          const r = await updateSpecimenRecord(tx, {
            identifier: props.identifier,
            externalIdentifiers: convertedExId,
            source: props.source,
          });
          return r;
        }
      );
    }

    // TODO: Check if it links to the correct person or change it
  }

  protected async syncLibrary(props: LibraryType) {
    const library = await selectLibraryByIdQuery(this.edgeDbClient, {
      libraryId: props.identifier,
    });
    // If library does not exist => insert one
    if (!library) {
      return systemAuditEventPattern(
        this.edgeDbClient,
        'C',
        `Insert new library record: ${props.identifier}`,
        async (tx: Transaction) => {
          const r = await insertLibraryRecord(tx, {
            ...props,
          });
          return r;
        }
      );
    }

    // // Check if specimen is the same with what we had in record and update if not
    // if (
    //   isSpecimenPropsNeedUpdate(
    //     {
    //       identifier: props.identifier,
    //       externalIdentifiers: <Record<string, string>>specimen.externalIdentifiers,
    //       source: specimen.source,
    //     },
    //     { ...props, externalIdentifiers: convertedExId }
    //   )
    // ) {
    //   return systemAuditEventPattern(
    //     this.edgeDbClient,
    //     'U',
    //     `Update existing specimen record: ${props.identifier}`,
    //     async (tx: Transaction) => {
    //       const r = await updateSpecimenRecord(tx, {
    //         identifier: props.identifier,
    //         externalIdentifiers: convertedExId,
    //         source: props.source,
    //       });
    //       return r;
    //     }
    //   );
    // }

    // TODO: Check if it links to the correct person or change it
  }

  public async syncGoogleMetadataRecords(
    sheetRecords: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ) {
    for (const rec of sheetRecords) {
      // Sync subject
      if (rec.SubjectID) {
        await this.syncSubject({
          identifier: rec.SubjectID,
          externalIdentifiers: rec.ExternalSubjectID ?? null,
        });
      }

      // Sync Sample
      if (rec.SampleID) {
        await this.syncSpecimen({
          identifier: rec.SampleID,
          externalIdentifiers: rec.ExternalSampleID ?? null,
          subjectId: rec.SubjectID ?? null,
          source: rec.Source ?? null,
        });
      }

      // Sync Library
      if (rec.LibraryID) {
        await this.syncLibrary({
          identifier: rec.LibraryID,
          phenotype: <metadata.Phenotype>rec.Phenotype ? <metadata.Phenotype>rec.Phenotype : null,
          workflow: <metadata.WorkflowTypes>rec.Workflow
            ? <metadata.WorkflowTypes>rec.Workflow
            : null,
          quality: <metadata.Quality>rec.Quality ? <metadata.Quality>rec.Quality : null,
          type: <metadata.LibraryTypes>rec.Type ? <metadata.LibraryTypes>rec.Type : null,
          assay: rec.Assay ? rec.Assay : null,
          coverage: rec['Coverage (X)'] ? <number>parseFloat(rec['Coverage (X)']) : null,
        });
      }
    }
  }

  // async downloadGoogleSpreadsheet() {}
}
// What if a person is half filling and value not completed yet?
