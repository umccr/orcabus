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
import {
  WgtsQcIcav2PipelineTable,
  WgtsQcIcav2PipelineTableStackProps,
} from './stacks/wgtsqc-pipeline-dynamo-db/deploy/stack';
import {
  TnIcav2PipelineTable,
  TnIcav2PipelineTableStackProps,
} from './stacks/tumor-normal-pipeline-dynamo-db/deploy/stack';
import {
  WtsIcav2PipelineTable,
  WtsIcav2PipelineTableStackProps,
} from './stacks/wts-dynamo-db/deploy/stack';
import {
  UmccriseIcav2PipelineTable,
  UmccriseIcav2PipelineTableStackProps,
} from './stacks/umccrise-pipeline-dynamo-db/deploy/stack';
import {
  RnasumIcav2PipelineTable,
  RnasumIcav2PipelineTableStackProps,
} from './stacks/rnasum-pipeline-dynamo-db/deploy/stack';
import {
  PierianDxPipelineTable,
  PierianDxPipelineTableStackProps,
} from './stacks/pieriandx-pipeline-dynamo-db/deploy';
import {
  AuthorizationManagerStack,
  AuthorizationManagerStackProps,
} from './stacks/authorization-manager/stack';
import {
  OncoanalyserNfPipelineTable,
  OncoanalyserNfPipelineTableStackProps,
} from './stacks/oncoanalyser-dynamodb/deploy/stack';
import {
  SashNfPipelineTable,
  SashNfPipelineTableStackProps,
} from './stacks/sash-dynamodb/deploy/stack';
import {
  OraCompressionIcav2PipelineTable,
  OraCompressionIcav2PipelineTableStackProps,
} from './stacks/ora-decompression-dynamodb/deploy/stack';
import {
  WorkflowTaskTokenTable,
  WorkflowTaskTokenTableStackProps,
} from './stacks/workflow-task-token-manager-dynamo-db/deploy';

export interface StatefulStackCollectionProps {
  dataBucketStackProps: DataBucketStackProps;
  authorizationManagerStackProps: AuthorizationManagerStackProps;
  sharedStackProps: SharedStackProps;
  postgresManagerStackProps: PostgresManagerStackProps;
  tokenServiceStackProps: TokenServiceStackProps;
  icaEventPipeStackProps: IcaEventPipeStackProps;
  bclconvertInteropQcIcav2PipelineTableStackProps: BclconvertInteropQcIcav2PipelineTableStackProps;
  cttsov2Icav2PipelineTableStackProps: Cttsov2Icav2PipelineTableStackProps;
  wgtsQcIcav2PipelineTableStackProps: WgtsQcIcav2PipelineTableStackProps;
  tnIcav2PipelineTableStackProps: TnIcav2PipelineTableStackProps;
  wtsIcav2PipelineTableStackProps: WtsIcav2PipelineTableStackProps;
  umccriseIcav2PipelineTableStackProps: UmccriseIcav2PipelineTableStackProps;
  rnasumIcav2PipelineTableStackProps: RnasumIcav2PipelineTableStackProps;
  oraCompressionIcav2PipelineTableStackProps: OraCompressionIcav2PipelineTableStackProps;
  BclConvertTableStackProps: BclConvertTableStackProps;
  stackyStatefulTablesStackProps: StackyStatefulTablesStackProps;
  pierianDxPipelineTableStackProps: PierianDxPipelineTableStackProps;
  oncoanalyserPipelineTableStackProps: OncoanalyserNfPipelineTableStackProps;
  sashPipelineTableStackProps: SashNfPipelineTableStackProps;
  workflowTaskTokenTableStackProps: WorkflowTaskTokenTableStackProps;
}

export class StatefulStackCollection {
  // You could add more stack here and initiate it at the constructor. See example below for reference

  readonly authorizationManagerStack: Stack;
  readonly dataBucketStack: Stack;
  readonly sharedStack: Stack;
  readonly postgresManagerStack: Stack;
  readonly tokenServiceStack: Stack;
  readonly icaEventPipeStack: Stack;
  readonly bclconvertInteropQcIcav2PipelineTableStack: Stack;
  readonly cttsov2Icav2PipelineTableStack: Stack;
  readonly wgtsQcIcav2PipelineTableStack: Stack;
  readonly tnIcav2PipelineTableStack: Stack;
  readonly wtsIcav2PipelineTableStack: Stack;
  readonly umccriseIcav2PipelineTableStack: Stack;
  readonly rnasumIcav2PipelineTableStack: Stack;
  readonly oraCompressionIcav2PipelineTableStack: Stack;
  readonly BclConvertTableStack: Stack;
  readonly stackyStatefulTablesStack: Stack;
  readonly pierianDxPipelineTableStack: Stack;
  readonly oncoanalyserPipelineTableStack: Stack;
  readonly sashPipelineTableStack: Stack;
  readonly workflowTaskTokenTableStack: Stack;

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

    this.authorizationManagerStack = new AuthorizationManagerStack(
      scope,
      'AuthorizationManagerStack',
      {
        ...this.createTemplateProps(env, 'AuthorizationManagerStack'),
        ...statefulConfiguration.authorizationManagerStackProps,
      }
    );

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

    this.wgtsQcIcav2PipelineTableStack = new WgtsQcIcav2PipelineTable(
      scope,
      'WgtsQcIcav2PipelineTableStack',
      {
        ...this.createTemplateProps(env, 'WgtsQcIcav2PipelineTableStack'),
        ...statefulConfiguration.wgtsQcIcav2PipelineTableStackProps,
      }
    );

    this.tnIcav2PipelineTableStack = new TnIcav2PipelineTable(scope, 'TnIcav2PipelineTableStack', {
      ...this.createTemplateProps(env, 'TnIcav2PipelineTableStack'),
      ...statefulConfiguration.tnIcav2PipelineTableStackProps,
    });

    this.wtsIcav2PipelineTableStack = new WtsIcav2PipelineTable(
      scope,
      'WtsIcav2PipelineTableStack',
      {
        ...this.createTemplateProps(env, 'WtsIcav2PipelineTableStack'),
        ...statefulConfiguration.wtsIcav2PipelineTableStackProps,
      }
    );

    this.umccriseIcav2PipelineTableStack = new UmccriseIcav2PipelineTable(
      scope,
      'UmccriseIcav2PipelineTableStack',
      {
        ...this.createTemplateProps(env, 'UmccriseIcav2PipelineTableStack'),
        ...statefulConfiguration.umccriseIcav2PipelineTableStackProps,
      }
    );

    this.rnasumIcav2PipelineTableStack = new RnasumIcav2PipelineTable(
      scope,
      'RnasumIcav2PipelineTableStack',
      {
        ...this.createTemplateProps(env, 'RnasumIcav2PipelineTableStack'),
        ...statefulConfiguration.rnasumIcav2PipelineTableStackProps,
      }
    );

    this.oraCompressionIcav2PipelineTableStack = new OraCompressionIcav2PipelineTable(
      scope,
      'OraCompressionIcav2PipelineTableStack',
      {
        ...this.createTemplateProps(env, 'OraCompressionIcav2PipelineTableStack'),
        ...statefulConfiguration.oraCompressionIcav2PipelineTableStackProps,
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

    this.pierianDxPipelineTableStack = new PierianDxPipelineTable(
      scope,
      'PierianDxPipelineTableStack',
      {
        ...this.createTemplateProps(env, 'PierianDxPipelineTableStack'),
        ...statefulConfiguration.pierianDxPipelineTableStackProps,
      }
    );

    this.oncoanalyserPipelineTableStack = new OncoanalyserNfPipelineTable(
      scope,
      'OncoanalyserNfPipelineTableStack',
      {
        ...this.createTemplateProps(env, 'OncoanalyserNfPipelineTableStack'),
        ...statefulConfiguration.oncoanalyserPipelineTableStackProps,
      }
    );

    this.sashPipelineTableStack = new SashNfPipelineTable(scope, 'SashNfPipelineTableStack', {
      ...this.createTemplateProps(env, 'SashNfPipelineTableStack'),
      ...statefulConfiguration.sashPipelineTableStackProps,
    });

    this.workflowTaskTokenTableStack = new WorkflowTaskTokenTable(
      scope,
      'WorkflowTaskTokenTableStack',
      {
        ...this.createTemplateProps(env, 'WorkflowTaskTokenTableStack'),
        ...statefulConfiguration.workflowTaskTokenTableStackProps,
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
