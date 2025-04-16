import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';
import { ITableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Cluster, TaskDefinition } from 'aws-cdk-lib/aws-ecs';
import { ContainerDefinition } from 'aws-cdk-lib/aws-ecs/lib/container-definition';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { IBucket } from 'aws-cdk-lib/aws-s3';
import { ApiGatewayConstructProps } from '../../../../components/api-gateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export interface EventDetailTypeProps {
  createJob: string;
  updateJob: string;
}

export type LambdaLayerList =
  | 'fileManagerLayer'
  | 'metadataLayer'
  | 'workflowManagerLayer'
  | 'fastqToolsLayer'
  | 'dataSharingToolsLayer';

export type LambdaNameList =
  | 'createCsvForS3StepsCopy'
  | 'createScriptFromPresignedUrlsList'
  | 'generatePresignedUrlsForDataObjects'
  | 'getFastqObjectFromFastqId'
  | 'getFileAndRelativePathFromS3AttributeId'
  | 'getFilesAndRelativePathsFromS3AttributeIds'
  | 'getLibraryObjectFromLibraryOrcabusId'
  | 'getS3DestinationAndSourceUriMappings'
  | 'getWorkflowFromPortalRunId'
  | 'handleWorkflowInputs'
  | 'getFastqsFromLibraryIdAndInstrumentRunIdList'
  | 'getFilesListFromPortalRunId'
  | 'listPortalRunIdsInLibrary'
  | 'queryAndCollectIcav2Prefixes'
  | 'updatePackagingJobApi'
  | 'updatePushJobApi'
  | 'uploadArchiveFileListAsCsv'
  | 'uploadPushJobToS3';

export type LambdaNameToLayerMappingType = { [key in LambdaNameList]: LambdaLayerList[] };

export interface LambdaFunctionProps {
  // Any lambda function with a layer will require the ssm and secrets
  hostnameSsmParameterObject: IStringParameter;
  orcabusTokenSecretObject: ISecret;
  // Some need to query the database
  packagingDynamoDbLookUpTable: ITableV2;
  packagingDynamoDbTableIndexName: string;
  // Others need to upload to s3 (csv to steps copy)
  s3StepsCopyBucket: IBucket;
  s3StepsCopyPrefix: string;
  // Others will need to upload to the packaging look up bucket
  packagingLookUpBucket: IBucket;
  packagingLookUpPrefix: string;
  pushLogsPrefix: string;
  // Athena properties
  athenaProps: AthenaWithBucketProps;
}

export const LambdaLayerToFunctionMapping: LambdaNameToLayerMappingType = {
  createCsvForS3StepsCopy: ['fileManagerLayer', 'dataSharingToolsLayer'],
  createScriptFromPresignedUrlsList: ['fileManagerLayer', 'dataSharingToolsLayer'],
  generatePresignedUrlsForDataObjects: ['fileManagerLayer'],
  getFastqObjectFromFastqId: ['fastqToolsLayer'],
  getFileAndRelativePathFromS3AttributeId: ['fileManagerLayer', 'dataSharingToolsLayer'],
  getFilesAndRelativePathsFromS3AttributeIds: ['fileManagerLayer', 'dataSharingToolsLayer'],
  getLibraryObjectFromLibraryOrcabusId: ['metadataLayer'],
  getS3DestinationAndSourceUriMappings: ['fileManagerLayer', 'dataSharingToolsLayer'],
  getWorkflowFromPortalRunId: [
    'workflowManagerLayer',
    'metadataLayer',
    'fileManagerLayer',
    'dataSharingToolsLayer',
  ],
  handleWorkflowInputs: [
    'metadataLayer',
    'fileManagerLayer',
    'fastqToolsLayer',
    'dataSharingToolsLayer',
  ],
  getFastqsFromLibraryIdAndInstrumentRunIdList: ['fastqToolsLayer', 'fileManagerLayer'],
  getFilesListFromPortalRunId: ['fileManagerLayer'],
  listPortalRunIdsInLibrary: [
    'workflowManagerLayer',
    'metadataLayer',
    'fileManagerLayer',
    'dataSharingToolsLayer',
  ],
  queryAndCollectIcav2Prefixes: ['fileManagerLayer', 'dataSharingToolsLayer'],
  updatePackagingJobApi: ['fileManagerLayer', 'dataSharingToolsLayer'],
  updatePushJobApi: ['fileManagerLayer', 'dataSharingToolsLayer'],
  uploadArchiveFileListAsCsv: ['fileManagerLayer', 'dataSharingToolsLayer'],
  uploadPushJobToS3: ['fileManagerLayer', 'dataSharingToolsLayer'],
};

export type DataPackagingLambdaNameList = Extract<
  LambdaNameList,
  // Starting lambdas
  | 'handleWorkflowInputs'
  | 'getLibraryObjectFromLibraryOrcabusId'
  // Handling api
  | 'updatePackagingJobApi'
  // Shared between fastq and secondary analysis
  | 'getFileAndRelativePathFromS3AttributeId'
  // Fastq lambdas
  | 'getFastqObjectFromFastqId'
  | 'getFastqsFromLibraryIdAndInstrumentRunIdList'
  // Secondary analysis lambdas
  | 'listPortalRunIdsInLibrary'
  | 'getWorkflowFromPortalRunId'
  | 'getFilesListFromPortalRunId'
>;

export type DataPresigningLambdaNameList = Extract<
  LambdaNameList,
  // Generate the presigned url
  'generatePresignedUrlsForDataObjects' | 'createScriptFromPresignedUrlsList'
>;

export type DataS3PushLambdaNameList = Extract<
  LambdaNameList,
  // Get the s3 destination and source uri mappings
  | 'getS3DestinationAndSourceUriMappings'
  // We also need to be able to upload the csv to the s3 steps copy bucket
  | 'createCsvForS3StepsCopy'
  // And update the jobs database
  | 'updatePushJobApiPy'
  // Permissions to upload the parquet log file to the packaging look up bucket
  | 'uploadPushJobToS3'
>;

export type DataICAv2PushLambdaNameList = Extract<
  LambdaNameList,
  // Get the s3 destination and source uri mappings
  'queryAndCollectIcav2Prefixes'
>;

export type DataPushLambdaNameList = Extract<
  LambdaNameList,
  // And update the jobs database
  'updatePushJobApi'
>;

export interface DataPackageReportOutputProps {
  cluster: Cluster;
  taskDefinition: TaskDefinition;
  container: ContainerDefinition;
  securityGroup: SecurityGroup;
}

export interface DataPackagingStateMachineFunctionProps {
  // Lambda list to be used in the state machine
  lambdas: { [key in DataPackagingLambdaNameList]: lambdaObject };
  // Bucket
  packagingLookUpBucket: IBucket;
  // DynamoDB table to be used in the state machine
  packageLookUpDb: ITableV2;
  packageLookUpTableIndexes: string[];
  // ECS task to be used in the state machine
  ecsTask: DataPackageReportOutputProps;
  // Event stuff
  eventBusProps: {
    eventBus: IEventBus;
    eventSource: string;
    fastqSyncEventDetailType: string;
  };
}

export interface DataPresigningStateMachineFunctionProps {
  // Lambda list to be used in the state machine
  lambdas: { [key in DataPresigningLambdaNameList]: lambdaObject };
  // Bucket
  packagingLookUpBucket: IBucket;
  // DynamoDB table to be used in the state machine
  packagingLookUpDb: ITableV2;
  packagingLookUpDbIndexNames: string[];
}

export interface DataPushS3StateMachineFunctionProps {
  // Lambda list to be used in the state machine
  lambdas: { [key in DataS3PushLambdaNameList]: lambdaObject };
  s3StepsCopyProps: S3StepsCopyProps;
}

export interface DataPushICAv2StateMachineFunctionProps {
  // Lambda list to be used in the state machine
  lambdas: { [key in DataICAv2PushLambdaNameList]: lambdaObject };
  eventBusProps: {
    eventBus: IEventBus;
    eventSource: string;
    icav2JobCopyEventDetailType: string;
  };
}

export interface DataPushStateMachineFunctionProps {
  lambdas: { [key in DataPushLambdaNameList]: lambdaObject };
  s3DataPushStateMachineProps: DataPushS3StateMachineFunctionProps;
  icav2DataPushStateMachineProps: DataPushICAv2StateMachineFunctionProps;
}

export interface S3StepsCopyProps {
  s3StepsCopyBucketName: string;
  s3StepsFunctionArn: string;
  s3StepsCopyPrefix: string;
}

export interface lambdaObjectProps {
  name: string;
  lambdaLayers: PythonLayerVersion[];
}

export interface lambdaObject extends lambdaObjectProps {
  lambdaFunction: lambda.Function;
}

export interface ecsTaskProps {
  packagingLookUpBucket: IBucket;
  packagingLookUpPrefix: string;
  packagingLookUpDynamoDbTable: ITableV2;
  packagingLookUpDynamoDbTableIndexNames: string[];
}

export interface AthenaProps {
  athenaS3BucketName: string;
  athenaS3Prefix: string;
  athenaWorkgroup: string;
  athenaDataSource: string;
  athenaDatabase: string;
  athenaLambdaFunctionName: string;
}

export interface AthenaWithBucketProps
  extends Omit<AthenaProps, 'athenaS3BucketName' | 'athenaLambdaFunctionName'> {
  athenaS3Bucket: IBucket;
  athenaLambdaFunction: lambda.IFunction;
}

export interface LambdaApiFunctionProps {
  // Layers
  dataSharingLayer: PythonLayerVersion;
  fileManagerLayer: PythonLayerVersion;
  // SSM And Secrets
  orcabusTokenSecretObj: ISecret;
  hostnameSsmParameterObj: IStringParameter;
  // Step functions
  packagingStateMachine: IStateMachine;
  presigningStateMachine: IStateMachine;
  pushStateMachine: IStateMachine;
  // Buckets
  packagingLookUpBucket: IBucket;
  packagingLookUpPrefix: string;
  // Event stuff
  eventBus: IEventBus;
  eventSource: string;
  eventDetailTypes: {
    packageEvents: EventDetailTypeProps;
    pushEvents: EventDetailTypeProps;
  };
  // Tables
  packagingDynamoDbApiTable: ITableV2;
  pushJobDynamoDbApiTable: ITableV2;
  // Table indexes
  packagingDynamoDbTableIndexNames: string[];
  pushJobDynamoDbTableIndexNames: string[];
  // custom domain name prefix
  customDomainNamePrefix: string;
}

export interface DataSharingStackConfig {
  /*
  Api stuff
  */
  apiGatewayCognitoProps: ApiGatewayConstructProps;
  /*
  S3 Bucket from stateful stack
  */
  packagingLookUpBucketName: string;
  packagingSharingPrefix: string;
  pushLogsPrefix: string;

  /* Get the hostname from the ssm parameter store */
  hostedZoneNameSsmParameterPath: string;

  /* Get the orcabus token from the secrets manager */
  orcabusTokenSecretsManagerPath: string;

  /*
  DynamoDB Table names from the stateful stack
  */
  // API-Backed Tables
  packagingDynamoDbApiTableName: string;
  packagingDynamoDbApiTableIndexNames: string[];
  pushJobDynamoDbApiTableName: string;
  pushJobDynamoDbTableIndexNames: string[];

  // Job look up table and data storage
  packagingLookUpDynamoDbTableName: string;
  packagingLookUpDynamoDbTableIndexNames: string[];

  /*
  s3StepsCopy Props
  */
  s3StepsCopyProps: S3StepsCopyProps;

  /*
  Event stuff
  */
  eventBusName: string;
  eventSource: string;
  eventDetailTypes: {
    packageEvents: EventDetailTypeProps;
    pushEvents: EventDetailTypeProps;
  };

  /*
  External event detail types used in the state machines
  for data pushing or unarchiving
  */
  fastqSyncDetailType: string;
  icav2JobCopyDetailType: string;

  /*
  Athena props
  */
  athenaProps: AthenaProps;
}
