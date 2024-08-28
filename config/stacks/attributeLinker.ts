import { AttributeLinkerProps } from '../../lib/workload/stateless/stacks/attribute-linker/deploy/stack';
import { eventBusName, vpcProps } from '../constants';

export const getAttributeLinkerProps = (): AttributeLinkerProps => {
  return {
    vpcProps,
    eventBusName,
  };
};
