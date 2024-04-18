import { BsRunsUploadManagerConfig } from '../../lib/workload/stateless/stacks/bs-runs-upload-manager/deploy/lib/stacks/bs_runs_upload_manager_stack';
import {
  devGdsBsRunsUploadLogPath,
  stgGdsBsRunsUploadLogPath,
  prodGdsBsRunsUploadLogPath,
  AccountName,
} from '../constants';

export const getBsRunsUploadManagerStackProps = (n: AccountName): BsRunsUploadManagerConfig => {
  const baseConfig = {
    ica_token_secret_id: 'IcaSecretsPortal',
    portal_token_secret_id: 'orcabus/token-service-jwt',
    basespace_token_secret_id: '/manual/BaseSpaceAccessTokenSecret',
    eventbus_name: '/umccr/orcabus/stateful/eventbridge',
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
