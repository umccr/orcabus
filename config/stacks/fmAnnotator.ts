import { FMAnnotatorProps } from '../../lib/workload/stateless/stacks/fmannotator/deploy/stack';
import {
  eventBusName,
  eventDlqNameFMAnnotator,
  fileManagerDomainPrefix,
  jwtSecretName,
  vpcProps,
} from '../constants';

export const getFmAnnotatorProps = (): FMAnnotatorProps => {
  return {
    vpcProps,
    eventBusName,
    jwtSecretName,
    eventDLQName: eventDlqNameFMAnnotator,
    customDomainNamePrefix: fileManagerDomainPrefix,
  };
};
