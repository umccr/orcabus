import { AttributeLinkerConfigurableProps } from '../../lib/workload/stateless/stacks/attribute-annotator/deploy/stack';
import { eventBusName, vpcProps } from '../constants';

export const getAttributeLinkerProps = (): AttributeLinkerConfigurableProps => {
  return {
    vpcProps,
    eventBusName,
  };
};
