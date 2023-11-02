import { Client } from 'edgedb';
import { metadata } from '../../../dbschema/interfaces';
import { inject, injectable } from 'tsyringe';
import { Logger } from 'pino';
import { JWT } from 'google-auth-library';
import { GetParameterCommand, SSMClient } from '@aws-sdk/client-ssm';
import { GoogleSpreadsheet } from 'google-spreadsheet';
import { MetadataRecords } from '../metadata';
import { getParameterDecryptedStoreWithLayerExtension } from '../../utils';

// This will tell from which year the system should query the worksheet
// The title of each sheet *SHOULD* be the year
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
  constructor(@inject('Logger') private readonly logger: Logger) {}
  /**
   * Get SpreadSheet values from Google Drive
   * @param sheetTitle
   * @returns
   */
  public async getSheetObject(
    sheetTitle: string
  ): Promise<Record<GoogleMetadataTrackingHeader, string | undefined>[]> {
    const googleAuthString = await getParameterDecryptedStoreWithLayerExtension(
      process.env.GDRIVE_SERVICE_ACCOUNT_PARAMETER_NAME
    );
    if (!googleAuthString) throw new Error('No GDrive credential found!');

    const googleSheetId = await getParameterDecryptedStoreWithLayerExtension(
      process.env.TRACKING_SHEET_ID_PARAMETER_NAME
    );
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

  public async downloadGoogleMetadata(): Promise<
    Record<GoogleMetadataTrackingHeader, string | undefined>[]
  > {
    let year = YEAR_START;
    let allRecords: Record<GoogleMetadataTrackingHeader, string | undefined>[] = [];

    // eslint-disable-next-line no-constant-condition
    while (true) {
      this.logger.info(`Retrieving Google Metadata Tracking Sheet year: ${year}`);

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

  public convertToMetadataRecord(
    googleRecArray: Record<GoogleMetadataTrackingHeader, string | undefined>[]
  ): MetadataRecords[] {
    this.logger.info('Converting all retrieved metadata to a recognized file format');

    return googleRecArray.map((rec) => {
      const val: MetadataRecords = {};

      if (rec.SubjectID) {
        val.subject = {
          internalId: rec.SubjectID,
          externalId: rec.ExternalSubjectID ?? null,
        };
      }

      if (rec.SampleID) {
        val.specimen = {
          internalId: rec.SampleID,
          externalId: rec.ExternalSampleID ?? null,
          source: rec.Source ?? null,
        };
      }

      if (rec.LibraryID) {
        val.library = {
          internalId: rec.LibraryID,
          phenotype: rec.Phenotype ? rec.Phenotype : null,
          workflow: <metadata.WorkflowTypes>rec.Workflow
            ? <metadata.WorkflowTypes>rec.Workflow
            : null,
          quality: rec.Quality ? rec.Quality : null,
          type: rec.Type ? rec.Type : null,
          assay: rec.Assay ? rec.Assay : null,
          coverage: rec['Coverage (X)'] ? rec['Coverage (X)'] : null,
        };
      }

      return val;
    });
  }
}
