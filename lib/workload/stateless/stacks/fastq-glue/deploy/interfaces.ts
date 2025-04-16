import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { IBucket } from 'aws-cdk-lib/aws-s3';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { bsshFastqCopyManagerWorkflowName } from '../../../../../../config/constants';

export interface CacheBucketProps {
  bucket: IBucket;
  prefix: string;
}

export type LambdaNameList =
  | 'createFastqSetObject' // Needs fastq_tools layer
  | 'getBclconvertDataFromSamplesheet' // Needs read access to cache bucket
  | 'getFileNamesFromFastqListCsv' // Needs read access to cache bucket
  | 'getSampleDemultiplexStats' // Needs read access to cache bucket
  | 'getSamplesFromSamplesheet'; // Needs read access to cache bucket

export interface lambdaObjectProps {
  needsCacheBucketReadPermissions: boolean;
  needsFastqToolsLayer: boolean;
}

export type LambdaToRequirementsMappingType = { [key in LambdaNameList]: lambdaObjectProps };

export const lambdaToRequirementsMapping: LambdaToRequirementsMappingType = {
  createFastqSetObject: {
    needsCacheBucketReadPermissions: false,
    needsFastqToolsLayer: true,
  },
  getBclconvertDataFromSamplesheet: {
    needsCacheBucketReadPermissions: true,
    needsFastqToolsLayer: false,
  },
  getFileNamesFromFastqListCsv: {
    needsCacheBucketReadPermissions: true,
    needsFastqToolsLayer: false,
  },
  getSampleDemultiplexStats: {
    needsCacheBucketReadPermissions: true,
    needsFastqToolsLayer: false,
  },
  getSamplesFromSamplesheet: {
    needsCacheBucketReadPermissions: true,
    needsFastqToolsLayer: false,
  },
};

export interface LambdaLayerRequirementsProps {
  hostnameSsmParameterObject: IStringParameter;
  orcabusTokenSecretObject: ISecret;
}

export interface LambdaBuilderInputProps {
  layerRequirements?: LambdaLayerRequirementsProps;
  fastqToolsLayer?: PythonLayerVersion;
  lambdaName: LambdaNameList;
  cacheBucketProps?: CacheBucketProps;
}

export interface lambdasBuilderInputProps {
  layerRequirements: LambdaLayerRequirementsProps;
  fastqToolsLayer: PythonLayerVersion;
  cacheBucketProps: CacheBucketProps;
  // Bit of a hack, to get the lab tracking metadata sheet
  metadataTrackingSheetIdSsmParameterObject: IStringParameter;
  gDriveAuthJsonSsmParameterObject: IStringParameter;
}

export interface FastqSetGenerationTemplateFunctionProps {
  eventBus: IEventBus;
  eventSource: string;
  eventDetailType: string;
}

export interface BsshFastqCopyToFastqSetCreationEventRuleProps {
  eventBus: IEventBus;
  eventSource: string;
  eventDetailType: string;
  eventStatus: string;
  eventWorkflowName: string;
  stateMachineTarget: IStateMachine;
}

export interface FastqGlueStackConfig {
  /*
  S3 Bucket from stateful stack
  */
  pipelineCacheBucketName: string;
  pipelineCachePrefix: string;

  /* Get the hostname from the ssm parameter store */
  hostedZoneNameSsmParameterPath: string;

  /* Get the orcabus token from the secrets manager */
  orcabusTokenSecretsManagerPath: string;

  /*
  Event stuff
  */
  eventBusName: string;
  eventSource: string;
  eventDetailType: string;

  /*
  External event information used to make event rules
  */
  workflowManagerEventSource: string;
  workflowRunStateChangeEventDetailType: string;
  bsshFastqCopyManagerWorkflowName: string;

  /*
  Couple of hacks to get topup/rerun information
  */
  gDriveAuthJsonSsmParameterPath: string;
  metadataTrackingSheetIdSsmParameterPath: string;
}
