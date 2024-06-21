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
  BsshIcav2FastqCopyManagerStack,
  BsshIcav2FastqCopyManagerStackProps,
} from './stacks/bssh-icav2-fastq-copy-manager/deploy/stack';
import {
  BclconvertInteropQcIcav2PipelineManagerStack,
  BclconvertInteropQcIcav2PipelineManagerStackProps,
} from './stacks/bclconvert-interop-qc-pipeline-manager/deploy/stack';
import {
  cttsov2Icav2PipelineManagerStackProps,
  Cttsov2Icav2PipelineManagerStack,
} from './stacks/cttso-v2-pipeline-manager/deploy/stack';
import { SchemaStack, SchemaStackProps } from './stacks/schema/stack';
import {
  BclConvertManagerStack,
  BclConvertManagerStackProps,
} from './stacks/bclconvert-manager/deploy/stack';
import {
  WorkflowManagerStack,
  WorkflowManagerStackProps,
} from './stacks/workflow-manager/deploy/stack';
import { GlueStack, GlueStackProps } from './stacks/stacky-mcstackface/glue-constructs';

export interface StatelessStackCollectionProps {
  postgresManagerStackProps: PostgresManagerStackProps;
  metadataManagerStackProps: MetadataManagerStackProps;
  sequenceRunManagerStackProps: SequenceRunManagerStackProps;
  fileManagerStackProps: FilemanagerProps;
  bsRunsUploadManagerStackProps: BsRunsUploadManagerStackProps;
  icav1CopyBatchUtilityStackProps: ICAv1CopyBatchUtilityStackProps;
  bsshIcav2FastqCopyManagerStackProps: BsshIcav2FastqCopyManagerStackProps;
  bclconvertInteropQcIcav2PipelineManagerStackProps: BclconvertInteropQcIcav2PipelineManagerStackProps;
  cttsov2Icav2PipelineManagerStackProps: cttsov2Icav2PipelineManagerStackProps;
  eventSchemaStackProps: SchemaStackProps;
  dataSchemaStackProps: SchemaStackProps;
  bclConvertManagerStackProps: BclConvertManagerStackProps;
  workflowManagerStackProps: WorkflowManagerStackProps;
  stackyMcStackFaceProps: GlueStackProps;
}

export class StatelessStackCollection {
  // You could add more stack here and initiate it at the constructor. See example below for reference
  readonly postgresManagerStack: Stack;
  readonly fileManagerStack: Stack;
  readonly metadataManagerStack: Stack;
  readonly sequenceRunManagerStack: Stack;
  readonly bsRunsUploadManagerStack: Stack;
  readonly icav1CopyBatchUtilityStack: Stack;
  readonly bsshIcav2FastqCopyManagerStack: Stack;
  readonly bclconvertInteropQcIcav2PipelineManagerStack: Stack;
  readonly cttsov2Icav2PipelineManagerStack: Stack;
  readonly eventSchemaStack: Stack;
  readonly dataSchemaStack: Stack;
  readonly bclConvertManagerStack: Stack;
  readonly workflowManagerStack: Stack;
  readonly stackyMcStackFaceStack: Stack;

  constructor(
    scope: Construct,
    env: Environment,
    statelessConfiguration: StatelessStackCollectionProps
  ) {
    this.eventSchemaStack = new SchemaStack(scope, 'EventSchemaStack', {
      ...this.createTemplateProps(env, 'EventSchemaStack'),
      ...statelessConfiguration.eventSchemaStackProps,
    });

    this.dataSchemaStack = new SchemaStack(scope, 'DataSchemaStack', {
      ...this.createTemplateProps(env, 'DataSchemaStack'),
      ...statelessConfiguration.dataSchemaStackProps,
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

    this.bsshIcav2FastqCopyManagerStack = new BsshIcav2FastqCopyManagerStack(
      scope,
      'BsshIcav2FastqCopyManagerStack',
      {
        ...this.createTemplateProps(env, 'BsshIcav2FastqCopyManagerStack'),
        ...statelessConfiguration.bsshIcav2FastqCopyManagerStackProps,
      }
    );

    this.bclconvertInteropQcIcav2PipelineManagerStack =
      new BclconvertInteropQcIcav2PipelineManagerStack(
        scope,
        'BclconvertInteropQcIcav2PipelineManagerStack',
        {
          ...this.createTemplateProps(env, 'BclconvertInteropQcIcav2PipelineManagerStack'),
          ...statelessConfiguration.bclconvertInteropQcIcav2PipelineManagerStackProps,
        }
      );

    this.cttsov2Icav2PipelineManagerStack = new Cttsov2Icav2PipelineManagerStack(
      scope,
      'Cttsov2Icav2PipelineManagerStack',
      {
        ...this.createTemplateProps(env, 'Cttsov2Icav2PipelineManagerStack'),
        ...statelessConfiguration.cttsov2Icav2PipelineManagerStackProps,
      }
    );

    this.bclConvertManagerStack = new BclConvertManagerStack(scope, 'BclConvertManagerStack', {
      ...this.createTemplateProps(env, 'BclConvertManagerStack'),
      ...statelessConfiguration.bclConvertManagerStackProps,
    });

    this.workflowManagerStack = new WorkflowManagerStack(scope, 'WorkflowManagerStack', {
      ...this.createTemplateProps(env, 'WorkflowManagerStack'),
      ...statelessConfiguration.workflowManagerStackProps,
    });
    this.stackyMcStackFaceStack = new GlueStack(scope, 'StackyMcStackFaceStack', {
      ...this.createTemplateProps(env, 'StackyMcStackFaceStack'),
      ...statelessConfiguration.stackyMcStackFaceProps,
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
