import { computeSecurityGroupName, eventBusName, vpcProps } from '../constants';
import { SequenceRunManagerStackProps } from '../../lib/workload/stateless/stacks/sequence-run-manager/deploy/component';

export const getSequenceRunManagerStackProps = (): SequenceRunManagerStackProps => {
  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
    mainBusName: eventBusName,
  };
};
