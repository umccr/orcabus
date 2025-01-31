import { FMAnnotatorConfigurableProps } from '../../lib/workload/stateless/stacks/fmannotator/deploy/stack';
import { eventBusName, eventDlqNameFMAnnotator, jwtSecretName, vpcProps } from '../constants';

export const getFmAnnotatorProps = (): FMAnnotatorConfigurableProps => {
  return {
    vpcProps,
    eventBusName,
    jwtSecretName,
    eventDLQName: eventDlqNameFMAnnotator,
  };
};
