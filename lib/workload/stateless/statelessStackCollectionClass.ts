import { Construct } from 'constructs';
import { Stack, Environment, StackProps } from 'aws-cdk-lib';

import { FilemanagerProps, Filemanager } from './stacks/filemanager/deploy/stack';

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
  BsshIcav2FastqCopyManagerStack,
  BsshIcav2FastqCopyManagerStackProps,
} from './stacks/bssh-icav2-fastq-copy-manager/deploy/stack';
import {
  BclconvertInteropQcIcav2PipelineManagerStack,
  BclconvertInteropQcIcav2PipelineManagerStackProps,
} from './stacks/bclconvert-interop-qc-pipeline-manager/deploy/stack';
import {
  Cttsov2Icav2PipelineManagerStackProps,
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
import {
  WgtsQcIcav2PipelineManagerStack,
  WgtsQcIcav2PipelineManagerStackProps,
} from './stacks/wgts-alignment-qc-pipeline-manager/deploy';
import {
  TnIcav2PipelineManagerStack,
  TnIcav2PipelineManagerStackProps,
} from './stacks/tumor-normal-pipeline-manager/deploy';
import {
  WtsIcav2PipelineManagerStack,
  WtsIcav2PipelineManagerStackProps,
} from './stacks/transcriptome-pipeline-manager/deploy';
import {
  UmccriseIcav2PipelineManagerStack,
  UmccriseIcav2PipelineManagerStackProps,
} from './stacks/umccrise-pipeline-manager/deploy';
import {
  RnasumIcav2PipelineManagerStack,
  RnasumIcav2PipelineManagerStackProps,
} from './stacks/rnasum-pipeline-manager/deploy';
import { FMAnnotator, FMAnnotatorConfigurableProps } from './stacks/fmannotator/deploy/stack';
import {
  PieriandxPipelineManagerStack,
  PierianDxPipelineManagerStackProps,
} from './stacks/pieriandx-pipeline-manager/deploy';

export interface StatelessStackCollectionProps {
  metadataManagerStackProps: MetadataManagerStackProps;
  sequenceRunManagerStackProps: SequenceRunManagerStackProps;
  fileManagerStackProps: FilemanagerProps;
  bsRunsUploadManagerStackProps: BsRunsUploadManagerStackProps;
  bsshIcav2FastqCopyManagerStackProps: BsshIcav2FastqCopyManagerStackProps;
  bclconvertInteropQcIcav2PipelineManagerStackProps: BclconvertInteropQcIcav2PipelineManagerStackProps;
  cttsov2Icav2PipelineManagerStackProps: Cttsov2Icav2PipelineManagerStackProps;
  wgtsQcIcav2PipelineManagerStackProps: WgtsQcIcav2PipelineManagerStackProps;
  tnIcav2PipelineManagerStackProps: TnIcav2PipelineManagerStackProps;
  wtsIcav2PipelineManagerStackProps: WtsIcav2PipelineManagerStackProps;
  umccriseIcav2PipelineManagerStackProps: UmccriseIcav2PipelineManagerStackProps;
  rnasumIcav2PipelineManagerStackProps: RnasumIcav2PipelineManagerStackProps;
  pieriandxPipelineManagerStackProps: PierianDxPipelineManagerStackProps;
  eventSchemaStackProps: SchemaStackProps;
  dataSchemaStackProps: SchemaStackProps;
  bclConvertManagerStackProps: BclConvertManagerStackProps;
  workflowManagerStackProps: WorkflowManagerStackProps;
  stackyMcStackFaceProps: GlueStackProps;
  fmAnnotatorProps: FMAnnotatorConfigurableProps;
}

export class StatelessStackCollection {
  // You could add more stack here and initiate it at the constructor. See example below for reference
  readonly fileManagerStack: Stack;
  readonly metadataManagerStack: Stack;
  readonly sequenceRunManagerStack: Stack;
  readonly bsRunsUploadManagerStack: Stack;
  readonly bsshIcav2FastqCopyManagerStack: Stack;
  readonly bclconvertInteropQcIcav2PipelineManagerStack: Stack;
  readonly cttsov2Icav2PipelineManagerStack: Stack;
  readonly wgtsQcIcav2PipelineManagerStack: Stack;
  readonly tnIcav2PipelineManagerStack: Stack;
  readonly wtsIcav2PipelineManagerStack: Stack;
  readonly umccriseIcav2PipelineManagerStack: Stack;
  readonly rnasumIcav2PipelineManagerStack: Stack;
  readonly pieriandxPipelineManagerStack: Stack;
  readonly eventSchemaStack: Stack;
  readonly dataSchemaStack: Stack;
  readonly bclConvertManagerStack: Stack;
  readonly workflowManagerStack: Stack;
  readonly stackyMcStackFaceStack: Stack;
  readonly fmAnnotator: Stack;

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

    const fileManagerStack = new Filemanager(scope, 'FileManagerStack', {
      ...this.createTemplateProps(env, 'FileManagerStack'),
      ...statelessConfiguration.fileManagerStackProps,
    });
    this.fileManagerStack = fileManagerStack;

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

    this.wgtsQcIcav2PipelineManagerStack = new WgtsQcIcav2PipelineManagerStack(
      scope,
      'WgtsQcIcav2PipelineManagerStack',
      {
        ...this.createTemplateProps(env, 'WgtsQcIcav2PipelineManagerStack'),
        ...statelessConfiguration.wgtsQcIcav2PipelineManagerStackProps,
      }
    );

    this.tnIcav2PipelineManagerStack = new TnIcav2PipelineManagerStack(
      scope,
      'TnIcav2PipelineManagerStack',
      {
        ...this.createTemplateProps(env, 'TnIcav2PipelineManagerStack'),
        ...statelessConfiguration.tnIcav2PipelineManagerStackProps,
      }
    );

    this.wtsIcav2PipelineManagerStack = new WtsIcav2PipelineManagerStack(
      scope,
      'WtsIcav2PipelineManagerStack',
      {
        ...this.createTemplateProps(env, 'WtsIcav2PipelineManagerStack'),
        ...statelessConfiguration.wtsIcav2PipelineManagerStackProps,
      }
    );

    this.umccriseIcav2PipelineManagerStack = new UmccriseIcav2PipelineManagerStack(
      scope,
      'UmccriseIcav2PipelineManagerStack',
      {
        ...this.createTemplateProps(env, 'UmccriseIcav2PipelineManagerStack'),
        ...statelessConfiguration.umccriseIcav2PipelineManagerStackProps,
      }
    );

    this.rnasumIcav2PipelineManagerStack = new RnasumIcav2PipelineManagerStack(
      scope,
      'RnasumIcav2PipelineManagerStack',
      {
        ...this.createTemplateProps(env, 'RnasumIcav2PipelineManagerStack'),
        ...statelessConfiguration.rnasumIcav2PipelineManagerStackProps,
      }
    );

    this.pieriandxPipelineManagerStack = new PieriandxPipelineManagerStack(
      scope,
      'PieriandxPipelineManagerStack',
      {
        ...this.createTemplateProps(env, 'PieriandxPipelineManagerStack'),
        ...statelessConfiguration.pieriandxPipelineManagerStackProps,
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

    this.fmAnnotator = new FMAnnotator(scope, 'FMAnnotatorStack', {
      ...this.createTemplateProps(env, 'FMAnnotatorStack'),
      ...statelessConfiguration.fmAnnotatorProps,
      domainName: fileManagerStack.domainName,
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
