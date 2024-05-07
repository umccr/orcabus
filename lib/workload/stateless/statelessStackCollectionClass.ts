import { Construct } from 'constructs';
import { Stack, Environment, StackProps } from 'aws-cdk-lib';

import { FilemanagerProps, Filemanager } from './stacks/filemanager/deploy/stack';
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
} from './stacks/sequence-run-manager/deploy/stack';
import {
  BsRunsUploadManagerStack,
  BsRunsUploadManagerStackProps,
} from './stacks/bs-runs-upload-manager/deploy/stack';
import {
  ICAv1CopyBatchUtilityStack,
  ICAv1CopyBatchUtilityStackProps,
} from './stacks/icav1-copy-batch-utility/deploy/stack';
import {
  ICAv2CopyBatchUtilityStack,
  ICAv2CopyBatchUtilityStackProps,
} from './stacks/icav2-copy-batch-utility/deploy/stack';
import {
  BsshIcav2FastqCopyManagerStack,
  BsshIcav2FastqCopyManagerStackProps,
} from './stacks/bssh-icav2-fastq-copy-manager/deploy/stack';
import { SchemaStack, SchemaStackProps } from './stacks/schema/stack';

export interface StatelessStackCollectionProps {
  postgresManagerStackProps: PostgresManagerStackProps;
  metadataManagerStackProps: MetadataManagerStackProps;
  sequenceRunManagerStackProps: SequenceRunManagerStackProps;
  fileManagerStackProps: FilemanagerProps;
  bsRunsUploadManagerStackProps: BsRunsUploadManagerStackProps;
  icav1CopyBatchUtilityStackProps: ICAv1CopyBatchUtilityStackProps;
  icav2CopyBatchUtilityStackProps: ICAv2CopyBatchUtilityStackProps;
  bsshIcav2FastqCopyManagerStackProps: BsshIcav2FastqCopyManagerStackProps;
  schemaStackProps: SchemaStackProps;
}

export class StatelessStackCollection {
  // You could add more stack here and initiate it at the constructor. See example below for reference
  readonly postgresManagerStack: Stack;
  readonly fileManagerStack: Stack;
  readonly metadataManagerStack: Stack;
  readonly sequenceRunManagerStack: Stack;
  readonly bsRunsUploadManagerStack: Stack;
  readonly icav1CopyBatchUtilityStack: Stack;
  readonly icav2CopyBatchUtilityStack: Stack;
  readonly bsshIcav2FastqCopyManagerStack: Stack;
  readonly schemaStack: Stack;

  constructor(
    scope: Construct,
    env: Environment,
    statelessConfiguration: StatelessStackCollectionProps
  ) {
    this.schemaStack = new SchemaStack(scope, 'SchemaStack', {
      ...this.createTemplateProps(env, 'SchemaStack'),
      ...statelessConfiguration.schemaStackProps,
    });

    this.postgresManagerStack = new PostgresManagerStack(scope, 'PostgresManagerStack', {
      ...this.createTemplateProps(env, 'PostgresManagerStack'),
      ...statelessConfiguration.postgresManagerStackProps,
    });

    this.fileManagerStack = new Filemanager(scope, 'FileManagerStack', {
      ...this.createTemplateProps(env, 'FileManagerStack'),
      ...statelessConfiguration.fileManagerStackProps,
    });

    this.metadataManagerStack = new MetadataManagerStack(scope, 'MetadataManagerStack', {
      ...this.createTemplateProps(env, 'MetadataManagerStack'),
      ...statelessConfiguration.metadataManagerStackProps,
    });

    this.sequenceRunManagerStack = new SequenceRunManagerStack(scope, 'SequenceRunManagerStack', {
      ...this.createTemplateProps(env, 'SequenceRunManagerStack'),
      ...statelessConfiguration.sequenceRunManagerStackProps,
    });

    this.bsRunsUploadManagerStack = new BsRunsUploadManagerStack(
      scope,
      'BsRunsUploadManagerStack',
      {
        ...this.createTemplateProps(env, 'BsRunsUploadManagerStack'),
        ...statelessConfiguration.bsRunsUploadManagerStackProps,
      }
    );
    this.icav1CopyBatchUtilityStack = new ICAv1CopyBatchUtilityStack(
      scope,
      'ICAv1CopyBatchUtilityStack',
      {
        ...this.createTemplateProps(env, 'ICAv1CopyBatchUtilityStack'),
        ...statelessConfiguration.icav1CopyBatchUtilityStackProps,
      }
    );
    this.icav2CopyBatchUtilityStack = new ICAv2CopyBatchUtilityStack(
      scope,
      'ICAv2CopyBatchUtilityStack',
      {
        ...this.createTemplateProps(env, 'ICAv2CopyBatchUtilityStack'),
        ...statelessConfiguration.icav2CopyBatchUtilityStackProps,
      }
    );

    this.bsshIcav2FastqCopyManagerStack = new BsshIcav2FastqCopyManagerStack(
      scope,
      'BsshIcav2FastqCopyManagerStack',
      {
        ...this.createTemplateProps(env, 'BsshIcav2FastqCopyManagerStack'),
        ...statelessConfiguration.bsshIcav2FastqCopyManagerStackProps,
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
