import { Construct } from 'constructs';
import { Stack, Environment } from 'aws-cdk-lib';

import { SharedStack, SharedStackProps } from './stacks/shared/stack';
import { TokenServiceProps, TokenServiceStack } from './stacks/token_service/deploy/stack';
import { IcaEventPipeStack, IcaEventPipeStackProps } from './stacks/ica_event_pipe/stack';

export interface StatefulStackCollectionProps {
  sharedStackProps: SharedStackProps;
  tokenServiceStackProps: TokenServiceProps;
  icaEventPipeStackProps: IcaEventPipeStackProps;
}

export class StatefulStackCollection {
  // Only defined stacks
  readonly sharedStack: Stack;
  readonly tokenServiceStack: Stack;
  readonly icaEventPipeStack: Stack;

  constructor(
    scope: Construct,
    env: Environment,
    statefulConfiguration: StatefulStackCollectionProps
  ) {
    this.sharedStack = new SharedStack(scope, 'SharedStack', {
      env: env,
      ...statefulConfiguration.sharedStackProps,
    });

    this.tokenServiceStack = new TokenServiceStack(scope, 'TokenServiceStack', {
      env: env,
      ...statefulConfiguration.tokenServiceStackProps,
    });

    this.icaEventPipeStack = new IcaEventPipeStack(scope, 'IcaEventPipeStack', {
      env: env,
      ...statefulConfiguration.icaEventPipeStackProps,
    });
  }
}
