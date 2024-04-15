import { Construct } from 'constructs';
import { Stack, Environment, StackProps } from 'aws-cdk-lib';

import { FilemanagerProps, Filemanager } from './stacks/filemanager/deploy/lib/filemanager';
import {
  PostgresManagerStack,
  PostgresManagerStackProps,
} from './stacks/postgres-manager/deploy/stack';
import {
  MetadataManagerStack,
  MetadataManagerStackProps,
} from './stacks/metadata-manager/deploy/stack';
import {
  SequenceRunManagerStack,
  SequenceRunManagerStackProps,
} from './stacks/sequence-run-manager/deploy/component';

export interface StatelessStackCollectionProps {
  postgresManagerStackProps: PostgresManagerStackProps;
  metadataManagerStackProps: MetadataManagerStackProps;
  sequenceRunManagerStackProps: SequenceRunManagerStackProps;
  fileManagerStackProps: FilemanagerProps;
}

export class StatelessStackCollection {
  // You could add more stack here and initiate it at the constructor. See example below for reference
  readonly postgresManagerStack: Stack;
  readonly fileManagerStack: Stack;
  readonly metadataManagerStack: Stack;
  readonly sequenceRunManagerStack: Stack;

  constructor(
    scope: Construct,
    env: Environment,
    statefulConfiguration: StatelessStackCollectionProps
  ) {
    console.log('the env:', env);

    this.postgresManagerStack = new PostgresManagerStack(scope, 'PostgresManagerStack', {
      ...this.createTemplateProps(env, 'PostgresManagerStack'),
      ...statefulConfiguration.postgresManagerStackProps,
    });

    // this.fileManagerStack = new Filemanager(scope, 'FileManagerStack', {
    //   ...this.createTemplateProps(env, 'FileManagerStack'),
    //   ...statefulConfiguration.fileManagerStackProps,
    // });

    this.metadataManagerStack = new MetadataManagerStack(scope, 'MetadataManagerStack', {
      ...this.createTemplateProps(env, 'MetadataManagerStack'),
      ...statefulConfiguration.metadataManagerStackProps,
    });

    this.sequenceRunManagerStack = new SequenceRunManagerStack(scope, 'SequenceRunManagerStack', {
      ...this.createTemplateProps(env, 'SequenceRunManagerStack'),
      ...statefulConfiguration.sequenceRunManagerStackProps,
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
