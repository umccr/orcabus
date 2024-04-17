import { computeSecurityGroupName, vpcProps } from '../constants';
import { MetadataManagerStackProps } from '../../lib/workload/stateless/stacks/metadata-manager/deploy/stack';

export const getMetadataManagerStackProps = (): MetadataManagerStackProps => {
  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
  };
};
