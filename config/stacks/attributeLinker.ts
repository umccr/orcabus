import { FMAnnotatorConfigurableProps } from '../../lib/workload/stateless/stacks/fmannotator/deploy/stack';
import { eventBusName, vpcProps } from '../constants';

export const getAttributeLinkerProps = (): FMAnnotatorConfigurableProps => {
  return {
    vpcProps,
    eventBusName,
  };
};
