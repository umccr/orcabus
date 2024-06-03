import {
  AppStage,
  icaAccessTokenSecretName,
  jwtSecretName,
  basespaceAccessTokenSecretName,
  eventBusName,
  gdsBsRunsUploadLogPath,
  ssCheckApiUrlSsmParameterName,
} from '../constants';
import { BsRunsUploadManagerConfig } from '../../lib/workload/stateless/stacks/bs-runs-upload-manager/deploy/stack';

export const getBsRunsUploadManagerStackProps = (stage: AppStage): BsRunsUploadManagerConfig => {
  return {
    icaTokenSecretId: icaAccessTokenSecretName,
    portalTokenSecretId: jwtSecretName,
    basespaceTokenSecretId: basespaceAccessTokenSecretName,
    ssCheckApiUrlSsmParameterName: ssCheckApiUrlSsmParameterName,
    eventbusName: eventBusName,
    gdsSystemFilesPath: gdsBsRunsUploadLogPath[stage],
  };
};
