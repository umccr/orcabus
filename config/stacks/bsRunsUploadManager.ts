import {
  devGdsBsRunsUploadLogPath,
  stgGdsBsRunsUploadLogPath,
  prodGdsBsRunsUploadLogPath,
  AccountName,
  icaAccessTokenSecretName,
  jwtSecretName,
  basespaceAccessTokenSecretName,
  eventBusName,
} from '../constants';
import { BsRunsUploadManagerConfig } from '../../lib/workload/stateless/stacks/bs-runs-upload-manager/deploy/stack';

export const getBsRunsUploadManagerStackProps = (n: AccountName): BsRunsUploadManagerConfig => {
  const baseConfig = {
    ica_token_secret_id: icaAccessTokenSecretName,
    portal_token_secret_id: jwtSecretName,
    basespace_token_secret_id: basespaceAccessTokenSecretName,
    eventbus_name: eventBusName,
  };

  switch (n) {
    case 'beta':
      return {
        ...baseConfig,
        gds_system_files_path: devGdsBsRunsUploadLogPath,
      };
    case 'gamma':
      return {
        ...baseConfig,
        gds_system_files_path: stgGdsBsRunsUploadLogPath,
      };
    case 'prod':
      return {
        ...baseConfig,
        gds_system_files_path: prodGdsBsRunsUploadLogPath,
      };
  }
};
