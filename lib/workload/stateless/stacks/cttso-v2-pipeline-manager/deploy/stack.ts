import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import { Cttsov2Icav2PipelineManagerConstruct } from './constructs/cttsov2-icav2-manager';
import path from 'path';
import { ICAv2CopyFilesConstruct } from '../../../../components/icav2-copy-files';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';
import { DockerImageCode, DockerImageFunction } from 'aws-cdk-lib/aws-lambda';
import { OraDecompressionConstruct } from '../../../../components/ora-file-decompression-fq-pair-sfn';

export interface Cttsov2Icav2PipelineManagerConfig {
  /* ICAv2 Pipeline analysis essentials */
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pipelineIdSsmPath: string; // List of parameters the workflow session state machine will need access to
  /* Table to store analyis metadata */
  dynamodbTableName: string;
  /* Internal and external buses */
  eventBusName: string;
  icaEventPipeName: string;
  /*
  Event handling
  */
  workflowType: string;
  workflowVersion: string;
  serviceVersion: string;
  triggerLaunchSource: string;
  internalEventSource: string;
  detailType: string;
  /*
  Names for statemachines
  */
  stateMachinePrefix: string;
}

export type Cttsov2Icav2PipelineManagerStackProps = Cttsov2Icav2PipelineManagerConfig &
  cdk.StackProps;

export class Cttsov2Icav2PipelineManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: Cttsov2Icav2PipelineManagerStackProps) {
    super(scope, id, props);

    // Get dynamodb table for construct
    const dynamodbTableObj = dynamodb.TableV2.fromTableName(
      this,
      'dynamodb_table',
      props.dynamodbTableName
    );

    // Get ICAv2 Access token secret object for construct
    const icav2AccessTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'icav2_secrets_object',
      props.icav2TokenSecretId
    );

    // Get the copy batch state machine name
    const icav2CopyFilesStateMachineObj = new ICAv2CopyFilesConstruct(
      this,
      'icav2_copy_files_state_machine_obj',
      {
        icav2JwtSecretParameterObj: icav2AccessTokenSecretObj,
        stateMachineName: `${props.stateMachinePrefix}-icav2-copy-files-sfn`,
      }
    );

    // Get the ora decompression construct
    const oraDecompressionStateMachineObj = new OraDecompressionConstruct(
      this,
      'ora_decompression_state_machine_obj',
      {
        icav2AccessTokenSecretId: icav2AccessTokenSecretObj.secretName,
        sfnPrefix: props.stateMachinePrefix,
      }
    );

    // Set ssm parameter object list
    const pipelineIdSsmObjList = ssm.StringParameter.fromStringParameterName(
      this,
      props.pipelineIdSsmPath,
      props.pipelineIdSsmPath
    );

    // Get event bus object
    const eventBusObj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    /*
        Build lambdas
    */

    /*
        Part 1: Set up the lambdas needed for the input json generation state machine
        Quite a bit more complicated than regular ICAv2 workflow setup since we need to
        1. Convert the samplesheet from json into csv format
        2. Upload the samplesheet to icav2
        3. Copy fastqs into a particular directory setup type
        4. Regulate how many fastqs are copied at a time given ICAv2 cannot limit this itself and falls over
    */

    const generateCopyManifestDictLambdaObj = new PythonFunction(
      this,
      'generate_copy_manifest_dict_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/generate_copy_manifest_dict_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_copy_manifest_dict.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    // upload_samplesheet_to_cache_dir_py lambda
    const uploadSamplesheetToCacheDirLambdaObj = new PythonFunction(
      this,
      'upload_samplesheet_to_cache_dir_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/upload_samplesheet_to_cache_dir_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'upload_samplesheet_to_cache_dir.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    const getRandomNumberLambdaObj = new PythonFunction(
      this,
      'get_random_number_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/get_random_number_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_random_number.py',
        handler: 'handler',
      }
    );

    // We need to add SFN_ARN to the env var list once we have it
    // We also need to update the permissions to allow this function to list executions
    const checkNumRunningSfns = new PythonFunction(
      this,
      'check_num_running_sfns_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/check_num_running_sfns_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'check_num_running_sfns.py',
        handler: 'handler',
      }
    );

    const checkFastqListRowIsOraLambdaObj = new PythonFunction(
      this,
      'check_fastq_list_row_is_ora_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/check_fastq_list_row_is_ora_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'check_fastq_list_row_is_ora.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    const convertOraToCacheUriGzPathLambdaObj = new PythonFunction(
      this,
      'convert_ora_to_cache_uri_gz_path_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/convert_ora_to_cache_uri_gz_path_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'convert_ora_to_cache_uri_gz_path.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    /*
    Part 2: Build lambdas for output json generation
    */

    // Delete the cache uri directory lambda
    const deleteCacheUriLambdaFunction = new PythonFunction(
      this,
      'delete_cache_uri_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/delete_cache_uri_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'delete_cache_uri.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    // Set the output json lambda
    const setOutputJsonLambdaFunction = new PythonFunction(
      this,
      'set_output_json_lambda_python_function',
      {
        entry: path.join(__dirname, '../lambdas/set_outputs_json_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'set_outputs_json.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(60),
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
        },
      }
    );

    // Get vcfs
    const getVcfsLambdaFunction = new PythonFunction(this, 'get_vcfs_lambda_python_function', {
      entry: path.join(__dirname, '../lambdas/find_all_vcf_files_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'find_all_vcf_files.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(60),
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
      },
    });

    // Compress vcf
    const architecture = lambda.Architecture.ARM_64;
    const compressVcfLambdaFunction = new DockerImageFunction(this, 'compress_vcf_lambda', {
      description: 'Compress Vcfs',
      code: DockerImageCode.fromImageAsset(path.join(__dirname, '../lambdas/compress_icav2_vcf'), {
        file: 'Dockerfile',
        buildArgs: {
          platform: architecture.dockerPlatform,
        },
      }),
      // GVCF test took about two minutes
      timeout: Duration.seconds(900), // Maximum length of lambda duration is 15 minutes
      retryAttempts: 0, // Never perform a retry if it fails
      memorySize: 2048, // Don't want pandas to kill the lambda
      architecture: architecture,
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
      },
    });

    // Check success lambda
    const checkSuccessLambdaFunction = new PythonFunction(this, 'check_success_lambda_function', {
      entry: path.join(__dirname, '../lambdas/check_success_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'check_success.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(60),
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
      },
    });

    // Create the state machine to launch the nextflow workflow on ICAv2
    const cttsov2LaunchStateMachine = new Cttsov2Icav2PipelineManagerConstruct(this, id, {
      /* Stack Objects */
      dynamodbTableObj: dynamodbTableObj,
      icav2AccessTokenSecretObj: icav2AccessTokenSecretObj,
      icav2CopyFilesStateMachineObj: icav2CopyFilesStateMachineObj.icav2CopyFilesSfnObj,
      oraDecompressionStateMachineObj: oraDecompressionStateMachineObj.sfnObject,
      pipelineIdSsmObj: pipelineIdSsmObjList,
      /* Lambdas paths */
      uploadSamplesheetToCacheDirLambdaObj: uploadSamplesheetToCacheDirLambdaObj, // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir_py'
      generateCopyManifestDictLambdaObj: generateCopyManifestDictLambdaObj, // __dirname + '/../../../lambdas/generate_copy_manifest_dict_py'
      getRandomNumberLambdaObj: getRandomNumberLambdaObj,
      checkNumRunningSfnsLambdaObj: checkNumRunningSfns,
      convertOraToCacheUriGzPathLambdaObj: convertOraToCacheUriGzPathLambdaObj,
      checkFastqListRowIsOraLambdaObj: checkFastqListRowIsOraLambdaObj,
      deleteCacheUriLambdaObj: deleteCacheUriLambdaFunction,
      setOutputJsonLambdaObj: setOutputJsonLambdaFunction,
      getVcfsLambdaObj: getVcfsLambdaFunction,
      compressVcfLambdaObj: compressVcfLambdaFunction,
      checkSuccessSampleLambdaObj: checkSuccessLambdaFunction,
      /* Step function templates */
      generateInputJsonSfnTemplatePath: path.join(
        __dirname,
        '../step_functions_templates/set_cttso_v2_nf_inputs.asl.json'
      ), // __dirname + '/../../../step_functions_templates/set_cttso_v2_nf_inputs.asl.json'
      generateOutputJsonSfnTemplatePath: path.join(
        __dirname,
        '../step_functions_templates/set_cttso_v2_nf_outputs.asl.json'
      ), // __dirname + '/../../../step_functions_templates/set_cttso_v2_nf_inputs.asl.json'
      /* Event buses */
      eventBusObj: eventBusObj,
      icaEventPipeName: props.icaEventPipeName,
      /* Event handling */
      detailType: props.detailType,
      serviceVersion: props.serviceVersion,
      triggerLaunchSource: props.triggerLaunchSource,
      internalEventSource: props.internalEventSource,
      stateMachinePrefix: props.stateMachinePrefix,
      workflowType: props.workflowType,
      workflowVersion: props.workflowVersion,
    });
  }
}
