import { aws_ec2 } from 'aws-cdk-lib';
import { Construct } from 'constructs';

export function getVpc(scope: Construct) {
  const vpcName = 'main-vpc';
  const vpcTags = {
    'Stack': 'networking',
  };

  return aws_ec2.Vpc.fromLookup(scope, 'MainVpc', {
    vpcName: scope.node.tryGetContext(vpcName),
    tags: vpcTags,
  });
}
