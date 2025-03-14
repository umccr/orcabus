import path from 'path';
import { Construct } from 'constructs';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { FilemanagerToolsPythonLambdaLayer } from '../../../../components/python-filemanager-tools-layer';
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { MetadataToolsPythonLambdaLayer } from '../../../../components/python-metadata-tools-layer';
import { IBucket, Bucket } from 'aws-cdk-lib/aws-s3';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import { WorkflowToolsPythonLambdaLayer } from '../../../../components/python-workflow-tools-layer';
import { FastqToolsPythonLambdaLayer } from '../../../../components/python-fastq-tools-layer';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

// Some globals
interface lambdaObjectProps {
  name: string;
  lambdaLayers: PythonLayerVersion[];
}

interface lambdaObject extends lambdaObjectProps {
  lambdaFunction: PythonFunction;
}

type lambdaLayerList =
  | 'fileManagerLayer'
  | 'metadataLayer'
  | 'workflowManagerLayer'
  | 'fastqToolsLayer'
  | 's3JsonToolsLayer';

type lambdaNameList =
  | 'checkFastqsAreArchived'
  | 'convertLimsJsonListToCsv'
  | 'createScriptFromPresignedUrlsList'
  | 'generatePresignedUrlForDataObjects'
  | 'generatePresignedUrlForSharingObjects'
  | 'getFileAndMetadataFromS3ObjectId'
  | 'getLibraryObjectFromLibraryOrcabusId'
  | 'getLimsRowFromLibrary'
  | 'getSecondaryAnalysisListFromLibrary'
  | 'getWorkflowFromPortalRunId'
  | 'handleWorkflowInputs'
  | 'listFastqsInLibraryAsFileIds'
  | 'listFilesListFromPortalRunId'
  | 'listPortalRunIdsInLibrary'
  | 'uploadArchiveFileListAsCsv';

type lambdaNameToLayerMappingType = { [key in lambdaNameList]: lambdaLayerList[] };

const lambdaLayerToFunctionMapping: lambdaNameToLayerMappingType = {
  checkFastqsAreArchived: ['fileManagerLayer', 's3JsonToolsLayer'],
  convertLimsJsonListToCsv: ['s3JsonToolsLayer'],
  createScriptFromPresignedUrlsList: [],
  generatePresignedUrlForDataObjects: [],
  generatePresignedUrlForSharingObjects: ['s3JsonToolsLayer'],
  getFileAndMetadataFromS3ObjectId: [
    'metadataLayer',
    'workflowManagerLayer',
    'fileManagerLayer',
    'fastqToolsLayer',
  ],
  getLibraryObjectFromLibraryOrcabusId: ['metadataLayer'],
  getLimsRowFromLibrary: ['metadataLayer', 'fastqToolsLayer'],
  getSecondaryAnalysisListFromLibrary: ['workflowManagerLayer'],
  getWorkflowFromPortalRunId: ['workflowManagerLayer'],
  handleWorkflowInputs: ['metadataLayer'],
  listFastqsInLibraryAsFileIds: ['fastqToolsLayer', 'fileManagerLayer'],
  listFilesListFromPortalRunId: ['fileManagerLayer'],
  listPortalRunIdsInLibrary: ['workflowManagerLayer'],
  uploadArchiveFileListAsCsv: ['s3JsonToolsLayer', 'fileManagerLayer'],
};

export interface DataSharingStackConfig {
  /*
  S3 Bucket from stateful stack
  */
  s3SharingBucketName: string;
  s3SharingPrefix: string;

  /*
  ICAv2 Access Token (need this for now since we are using the ICAv2 API to generate long-lived presigned urls)
  Until the FileManager is capable of doing so.
  */
  icav2AccessTokenSecretsManagerPath: string;

  /* Get the hostname from the ssm parameter store */
  hostedZoneNameSsmParameterPath: string;

  /* Get the orcabus token from the secrets manager */
  orcabusTokenSecretsManagerPath: string;
}

export type DataSharingStackProps = DataSharingStackConfig & cdk.StackProps;

export class DataSharingStack extends Stack {
  public readonly s3SharingBucket: IBucket;
  public readonly s3SharingPrefix: string;
  public readonly lambdaLayerPrefix: 'ds'; // Data Sharing
  public lambdaLayers: { [key in lambdaLayerList]: PythonLayerVersion };
  public readonly lambdaObjects: { [key in lambdaNameList]: lambdaObject };

  constructor(scope: Construct, id: string, props: StackProps & DataSharingStackProps) {
    super(scope, id, props);

    // Get the bucket object
    this.s3SharingBucket = Bucket.fromBucketName(
      this,
      's3-sharing-bucket',
      props.s3SharingBucketName
    );
    this.s3SharingPrefix = props.s3SharingPrefix;

    // Create the tool layers
    this.createToolLayers();

    /*
    Collect the required secret and ssm parameters for getting metadata
    */
    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      props.hostedZoneNameSsmParameterPath
    );
    const orcabusTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'orcabus_token_secret',
      props.orcabusTokenSecretsManagerPath
    );
    const icav2AccessTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'icav2_access_token_secret',
      props.icav2AccessTokenSecretsManagerPath
    );

    // Create the lambda functions
    this.createLambdaFunctions(hostnameSsmParameterObj, orcabusTokenSecretObj);

    // Edit lambda functions as necessary
    // Edit 1:
    // Generate Presigned Url for data objects needs icav2 access token permissions
    this.lambdaObjects.generatePresignedUrlForDataObjects.lambdaFunction.addEnvironment(
      'ICAV2_ACCESS_TOKEN_SECRET_ID',
      icav2AccessTokenSecretObj.secretName
    );
    // And give the lambda function permissions to read the secret
    icav2AccessTokenSecretObj.grantRead(
      this.lambdaObjects.generatePresignedUrlForDataObjects.lambdaFunction.currentVersion
    );

    // Create the aws step function
    const sharingStateMachine = new sfn.StateMachine(this, 'dataSharingSfn', {
      // State Machine Name
      stateMachineName: 'dataSharingSfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/sharing_sfn_template.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: this.createDefinitionSubstitutions(),
    });

    // Grant invoke permissions to the state machine for all lambda functions
    let lambdaName: keyof typeof this.lambdaObjects;
    for (lambdaName in this.lambdaObjects) {
      this.lambdaObjects[lambdaName].lambdaFunction.grantInvoke(sharingStateMachine);
    }

    // Give the state machine permissions to read / write to the data sharing bucket
    // At the sharingPrefix
    this.s3SharingBucket.grantReadWrite(sharingStateMachine, `${this.s3SharingPrefix}*`);
  }

  private camelCaseToSnakeCase(camelCase: string): string {
    return camelCase.replace(/([A-Z])/g, '_$1').toLowerCase();
  }

  private createToolLayers() {
    // Create the layers
    this.lambdaLayers = {
      fileManagerLayer: new FilemanagerToolsPythonLambdaLayer(this, 'filemanager-tools-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      metadataLayer: new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      workflowManagerLayer: new WorkflowToolsPythonLambdaLayer(this, 'workflow-manager-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      fastqToolsLayer: new FastqToolsPythonLambdaLayer(this, 'fastq-tools-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      s3JsonToolsLayer: new PythonLambdaLayerConstruct(this, 's3-json-tools-layer', {
        layerName: 's3JsonToolsLayer',
        layerDescription: 'layer to add in some functions on uploading s3 files',
        layerDirectory: path.join(__dirname, '../layers'),
      }).lambdaLayerVersionObj,
    };
  }

  private createLambdaObject(lambdaObject: lambdaObjectProps): lambdaObject {
    const lambdaNameToSnakeCase = this.camelCaseToSnakeCase(lambdaObject.name);
    const lambdaFunction = new PythonUvFunction(this, lambdaObject.name, {
      entry: path.join(__dirname, lambdaNameToSnakeCase + '_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: lambdaNameToSnakeCase + '.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
      layers: lambdaObject.lambdaLayers,
    });

    return {
      name: lambdaObject.name,
      lambdaLayers: lambdaObject.lambdaLayers,
      lambdaFunction: lambdaFunction,
    };
  }

  private createLambdaFunctions(
    hostnameSsmParamObject: ssm.IStringParameter,
    orcabusTokenSecretObject: secretsmanager.ISecret
  ) {
    // Iterate over lambdaLayerToMapping and create the lambda functions
    let lambdaName: keyof typeof lambdaLayerToFunctionMapping;
    for (lambdaName in lambdaLayerToFunctionMapping) {
      const lambdaLayers = lambdaLayerToFunctionMapping[lambdaName].map((layerName) => {
        return this.lambdaLayers[layerName];
      });

      const lambdaObject = this.createLambdaObject({
        name: lambdaName,
        lambdaLayers: lambdaLayers,
      });

      // Add environment variables
      lambdaObject.lambdaFunction.addEnvironment(
        'HOSTNAME_SSM_PARAMETER',
        hostnameSsmParamObject.parameterName
      );
      lambdaObject.lambdaFunction.addEnvironment(
        'ORCABUS_TOKEN_SECRET_ID',
        orcabusTokenSecretObject.secretName
      );

      // Add permissions to the lambda function
      hostnameSsmParamObject.grantRead(lambdaObject.lambdaFunction.currentVersion);
      orcabusTokenSecretObject.grantRead(lambdaObject.lambdaFunction.currentVersion);

      // Assign the lambda object to the lambdaObjects
      this.lambdaObjects[lambdaName] = lambdaObject;
    }
  }

  private createDefinitionSubstitutions(): { [key: string]: string } {
    const definitionSubstitutions: { [key: string]: string } = {
      __sharing_bucket__: this.s3SharingBucket.bucketName,
      __sharing_prefix__: this.s3SharingPrefix,
    };

    let lambdaName: keyof typeof this.lambdaObjects;
    for (lambdaName in this.lambdaObjects) {
      const lambdaObject = this.lambdaObjects[lambdaName];
      const sfnSubtitutionKey = `__${this.camelCaseToSnakeCase(lambdaObject.name)}_lambda_function_arn__`;
      definitionSubstitutions[sfnSubtitutionKey] =
        lambdaObject.lambdaFunction.currentVersion.functionArn;
    }

    return definitionSubstitutions;
  }
}
