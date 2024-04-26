import {
  devGdsBsRunsUploadLogPath,
  stgGdsBsRunsUploadLogPath,
  prodGdsBsRunsUploadLogPath,
  AppStage,
  icaAccessTokenSecretName,
  jwtSecretName,
  basespaceAccessTokenSecretName,
  eventBusName,
} from '../constants';
import { BsRunsUploadManagerConfig } from '../../lib/workload/stateless/stacks/bs-runs-upload-manager/deploy/stack';

export const getBsRunsUploadManagerStackProps = (n: AppStage): BsRunsUploadManagerConfig => {
  const baseConfig = {
    ica_token_secret_id: icaAccessTokenSecretName,
    portal_token_secret_id: jwtSecretName,
    basespace_token_secret_id: basespaceAccessTokenSecretName,
    eventbus_name: eventBusName,
  };

  switch (n) {
    case AppStage.BETA:
      return {
        ...baseConfig,
        gds_system_files_path: devGdsBsRunsUploadLogPath,
      };
    case AppStage.GAMMA:
      return {
        ...baseConfig,
        gds_system_files_path: stgGdsBsRunsUploadLogPath,
      };
    case AppStage.PROD:
      return {
        ...baseConfig,
        gds_system_files_path: prodGdsBsRunsUploadLogPath,
      };
  }
};
