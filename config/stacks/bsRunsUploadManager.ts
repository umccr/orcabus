import {
  AppStage,
  icaAccessTokenSecretName,
  jwtSecretName,
  basespaceAccessTokenSecretName,
  eventBusName,
  gdsBsRunsUploadLogPath,
  ssCheckApiDomainSsmParameterName,
} from '../constants';
import { BsRunsUploadManagerConfig } from '../../lib/workload/stateless/stacks/bs-runs-upload-manager/deploy/stack';

export const getBsRunsUploadManagerStackProps = (stage: AppStage): BsRunsUploadManagerConfig => {
  return {
    icaTokenSecretId: icaAccessTokenSecretName,
    portalTokenSecretId: jwtSecretName,
    basespaceTokenSecretId: basespaceAccessTokenSecretName,
    ssCheckApiDomainSsmParameterName: ssCheckApiDomainSsmParameterName,
    eventbusName: eventBusName,
    gdsSystemFilesPath: gdsBsRunsUploadLogPath[stage],
  };
};
