import {
  AppStage,
  icaAccessTokenSecretName,
  jwtSecretName,
  basespaceAccessTokenSecretName,
  eventBusName,
  gdsBsRunsUploadLogPath,
} from '../constants';
import { BsRunsUploadManagerConfig } from '../../lib/workload/stateless/stacks/bs-runs-upload-manager/deploy/stack';

export const getBsRunsUploadManagerStackProps = (stage: AppStage): BsRunsUploadManagerConfig => {
  return {
    ica_token_secret_id: icaAccessTokenSecretName,
    portal_token_secret_id: jwtSecretName,
    basespace_token_secret_id: basespaceAccessTokenSecretName,
    eventbus_name: eventBusName,
    gds_system_files_path: gdsBsRunsUploadLogPath[stage],
  };
};
