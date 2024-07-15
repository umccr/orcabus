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
  BclConvertTable,
  BclConvertTableStackProps,
} from './stacks/bclconvert-dynamo-db/deploy/stack';
import {
  BclconvertInteropQcIcav2PipelineTableStack,
  BclconvertInteropQcIcav2PipelineTableStackProps,
} from './stacks/bclconvert-interop-qc-pipeline-dynamo-db/deploy/stack';
import {
  StackyStatefulTablesStack,
  StackyStatefulTablesStackProps,
} from './stacks/stacky-mcstackface-dynamodb';
import {
  PostgresManagerStack,
  PostgresManagerStackProps,
} from './stacks/postgres-manager/deploy/stack';
import { DataBucketStack, DataBucketStackProps } from './stacks/data/stack';

export interface StatefulStackCollectionProps {
  dataBucketStackProps: DataBucketStackProps;
  sharedStackProps: SharedStackProps;
  postgresManagerStackProps: PostgresManagerStackProps;
  tokenServiceStackProps: TokenServiceStackProps;
  icaEventPipeStackProps: IcaEventPipeStackProps;
  bclconvertInteropQcIcav2PipelineTableStackProps: BclconvertInteropQcIcav2PipelineTableStackProps;
  cttsov2Icav2PipelineTableStackProps: Cttsov2Icav2PipelineTableStackProps;
  BclConvertTableStackProps: BclConvertTableStackProps;
  stackyStatefulTablesStackProps: StackyStatefulTablesStackProps;
}

export class StatefulStackCollection {
  // You could add more stack here and initiate it at the constructor. See example below for reference

  readonly dataBucketStack: Stack;
  readonly sharedStack: Stack;
  readonly postgresManagerStack: Stack;
  readonly tokenServiceStack: Stack;
  readonly icaEventPipeStack: Stack;
  readonly bclconvertInteropQcIcav2PipelineTableStack: Stack;
  readonly cttsov2Icav2PipelineTableStack: Stack;
  readonly BclConvertTableStack: Stack;
  readonly stackyStatefulTablesStack: Stack;

  constructor(
    scope: Construct,
    env: Environment,
    statefulConfiguration: StatefulStackCollectionProps
  ) {
    // Currently this only needs to be deployed if bucketName exist as props
    if (statefulConfiguration.dataBucketStackProps.bucketName) {
      this.dataBucketStack = new DataBucketStack(scope, 'DataBucketStack', {
        ...this.createTemplateProps(env, 'DataBucketStack'),
        ...statefulConfiguration.dataBucketStackProps,
      });
    }

    this.sharedStack = new SharedStack(scope, 'SharedStack', {
      ...this.createTemplateProps(env, 'SharedStack'),
      ...statefulConfiguration.sharedStackProps,
    });

    this.postgresManagerStack = new PostgresManagerStack(scope, 'PostgresManagerStack', {
      ...this.createTemplateProps(env, 'PostgresManagerStack'),
      ...statefulConfiguration.postgresManagerStackProps,
    });

    this.tokenServiceStack = new TokenServiceStack(scope, 'TokenServiceStack', {
      ...this.createTemplateProps(env, 'TokenServiceStack'),
      ...statefulConfiguration.tokenServiceStackProps,
    });

    this.icaEventPipeStack = new IcaEventPipeStack(scope, 'IcaEventPipeStack', {
      ...this.createTemplateProps(env, 'IcaEventPipeStack'),
      ...statefulConfiguration.icaEventPipeStackProps,
    });

    this.bclconvertInteropQcIcav2PipelineTableStack =
      new BclconvertInteropQcIcav2PipelineTableStack(
        scope,
        'BclconvertInteropQcIcav2PipelineTableStack',
        {
          ...this.createTemplateProps(env, 'BclconvertInteropQcIcav2PipelineTable'),
          ...statefulConfiguration.bclconvertInteropQcIcav2PipelineTableStackProps,
        }
      );

    this.cttsov2Icav2PipelineTableStack = new Cttsov2Icav2PipelineTable(
      scope,
      'Cttsov2Icav2PipelineTableStack',
      {
        ...this.createTemplateProps(env, 'Cttsov2Icav2PipelineTableStack'),
        ...statefulConfiguration.cttsov2Icav2PipelineTableStackProps,
      }
    );
    this.BclConvertTableStack = new BclConvertTable(scope, 'BclConvertTableStack', {
      ...this.createTemplateProps(env, 'BclConvertTableStack'),
      ...statefulConfiguration.BclConvertTableStackProps,
    });
    this.stackyStatefulTablesStack = new StackyStatefulTablesStack(
      scope,
      'StackyStatefulTablesStack',
      {
        ...this.createTemplateProps(env, 'StackyStatefulTablesStack'),
        ...statefulConfiguration.stackyStatefulTablesStackProps,
      }
    );
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
