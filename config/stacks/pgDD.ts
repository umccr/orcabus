import {
  accountIdAlias,
  AppStage,
  computeSecurityGroupName,
  rdsMasterSecretName,
  region,
  vpcProps,
} from '../constants';
import { PgDDStackProps } from '../../lib/workload/stateless/stacks/pg-dd/deploy/stack';
import { getDataBucketStackProps } from './dataBucket';

export const getPgDDProps = (stage: AppStage): PgDDStackProps | undefined => {
  const bucket = getDataBucketStackProps(stage);
  if (bucket.bucketName === undefined) {
    return undefined;
  } else {
    return {
      bucket: bucket.bucketName,
      prefix: 'pg-dd',
      secretArn: `arn:aws:secretsmanager:${region}:${accountIdAlias.beta}:secret:${rdsMasterSecretName}`, // pragma: allowlist secret
      lambdaSecurityGroupName: computeSecurityGroupName,
      vpcProps,
    };
  }
};
