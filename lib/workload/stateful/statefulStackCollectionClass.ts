import { Construct } from 'constructs';
import { Stack, Environment, StackProps } from 'aws-cdk-lib';

import { SharedStack, SharedStackProps } from './stacks/shared/stack';
import { TokenServiceStackProps, TokenServiceStack } from './stacks/token-service/deploy/stack';
import { IcaEventPipeStack, IcaEventPipeStackProps } from './stacks/ica-event-pipe/stack';
import {
  Cttsov2Icav2PipelineTable,
  Cttsov2Icav2PipelineTableStackProps,
} from './stacks/cttso-v2-pipeline-dynamo-db/deploy/stack';
import {
  Icav2EventTranslatorTable,
  Icav2EventTranslatorTableStackProps,
} from './stacks/icav2-event-translator-dynamo-db/deploy/stack';
import {StackyStatefulTablesStack, StackyStatefulTablesStackProps} from "./stacks/stacky-mcstackface-dynamodb";

export interface StatefulStackCollectionProps {
  sharedStackProps: SharedStackProps;
  tokenServiceStackProps: TokenServiceStackProps;
  icaEventPipeStackProps: IcaEventPipeStackProps;
  cttsov2Icav2PipelineTableStackProps: Cttsov2Icav2PipelineTableStackProps;
  icav2EventTranslatorTableStackProps: Icav2EventTranslatorTableStackProps;
  stackyStatefulTablesStackProps: StackyStatefulTablesStackProps;
}

export class StatefulStackCollection {
  // You could add more stack here and initiate it at the constructor. See example below for reference

  readonly sharedStack: Stack;
  readonly tokenServiceStack: Stack;
  readonly icaEventPipeStack: Stack;
  readonly cttsov2Icav2PipelineTableStack: Stack;
  readonly icav2EventTranslatorTableStack: Stack;
  readonly stackyStatefulTablesStack: Stack;

  constructor(
    scope: Construct,
    env: Environment,
    statefulConfiguration: StatefulStackCollectionProps
  ) {
    this.sharedStack = new SharedStack(scope, 'SharedStack', {
      ...this.createTemplateProps(env, 'SharedStack'),
      ...statefulConfiguration.sharedStackProps,
    });

    this.tokenServiceStack = new TokenServiceStack(scope, 'TokenServiceStack', {
      ...this.createTemplateProps(env, 'TokenServiceStack'),
      ...statefulConfiguration.tokenServiceStackProps,
    });

    this.icaEventPipeStack = new IcaEventPipeStack(scope, 'IcaEventPipeStack', {
      ...this.createTemplateProps(env, 'IcaEventPipeStack'),
      ...statefulConfiguration.icaEventPipeStackProps,
    });

    this.cttsov2Icav2PipelineTableStack = new Cttsov2Icav2PipelineTable(
      scope,
      'Cttsov2Icav2PipelineTableStack',
      {
        ...this.createTemplateProps(env, 'Cttsov2Icav2PipelineTableStack'),
        ...statefulConfiguration.cttsov2Icav2PipelineTableStackProps,
      }
    );
    this.icav2EventTranslatorTableStack = new Icav2EventTranslatorTable(
      scope,
      'Icav2EventTranslatorTableStack',
      {
        ...this.createTemplateProps(env, 'Icav2EventTranslatorTableStack'),
        ...statefulConfiguration.icav2EventTranslatorTableStackProps,
      }
    );

    this.stackyStatefulTablesStack = new StackyStatefulTablesStack(scope, 'StackyStatefulTablesStack', {
      ...this.createTemplateProps(env, 'StackyStatefulTablesStack'),
      ...statefulConfiguration.stackyStatefulTablesStackProps,
    });

  }

  /**
   * This output the StackProps that each stack should have on deployment
   *
   * @param env The environment which each stack should deploy to
   * @param serviceName The service name
   * @returns StackProps that will be included as template
   */
  private createTemplateProps(env: Environment, serviceName: string): StackProps {
    return {
      env: env,
      tags: {
        'umccr-org:Product': 'OrcaBus',
        'umccr-org:Creator': 'CDK',
        'umccr-org:Service': serviceName,
      },
    };
  }
}
