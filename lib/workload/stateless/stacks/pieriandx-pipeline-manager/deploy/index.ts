import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PieriandxLaunchStepFunctionStateMachineConstruct } from './constructs/pieriandx_launch_step_function';
import { PieriandxLaunchCaseCreationStepFunctionStateMachineConstruct } from './constructs/pieriandx_launch_case_creation_step_function';
import { PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstruct } from './constructs/pieriandx_launch_informaticsjob_creation_step_function';
import { PieriandxLaunchSequencerrunCreationStepFunctionsStateMachineConstruct } from './constructs/pieriandx_launch_sequencerrun_creation_step_function';
import * as path from 'path';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Duration } from 'aws-cdk-lib';
import { PieriandxMonitorRunsStepFunctionStateMachineConstruct } from './constructs/pieriandx_monitor_runs_step_function';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import { NagSuppressions } from 'cdk-nag';

export interface PierianDxPipelineManagerConfig {
  /* DynamoDB Table */
  dynamodbTableName: string;
  /* Workflow knowledge */
  workflowName: string;
  workflowVersion: string;
  /* Default values */
  defaultDagVersion: string;
  defaultPanelName: string;
  /* Secrets */
  icav2AccessTokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  pieriandxS3AccessTokenSecretId: string; // "/pieriandx/s3AccessCredentials"
  /* SSM Parameters */
  dagSsmParameterPath: string;
  panelNameSsmParameterPath: string;
  s3SequencerRunRootSsmParameterPath: string;
  /*
    Pieriandx specific parameters
    */
  pieriandxUserEmailSsmParameterPath: string;
  pieriandxInstitutionSsmParameterPath: string;
  pieriandxBaseUrlSsmParameterPath: string;
  pieriandxAuthTokenCollectionLambdaFunctionName: string;
  /* Event info */
  eventDetailType: string;
  eventBusName: string;
  eventSource: string;
  payloadVersion: string;
  triggerLaunchSource: string;
  /* Custom */
  prefix: string;
}

export type PierianDxPipelineManagerStackProps = PierianDxPipelineManagerConfig & cdk.StackProps;

export class PieriandxPipelineManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: PierianDxPipelineManagerStackProps) {
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
      'Icav2SecretsObject',
      props.icav2AccessTokenSecretId
    );

    const pieriandxS3AccessTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'PieriandxS3SecretsObject',
      props.pieriandxS3AccessTokenSecretId
    );

    /*
        Get the ssm parameters
        */
    const dagSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'dag',
      props.dagSsmParameterPath
    );
    const panelNameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'panel_name',
      props.panelNameSsmParameterPath
    );
    const s3SequencerRunRootSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      's3_sequencerrun_root',
      props.s3SequencerRunRootSsmParameterPath
    );

    /*
        Get the pieriandx parameters
        */
    const pieriandxUserEmailSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'pieriandx_useremail',
      props.pieriandxUserEmailSsmParameterPath
    );
    const pieriandxInstitutionSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'pieriandx_institution',
      props.pieriandxInstitutionSsmParameterPath
    );
    const pieriandxBaseUrlSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'pieriandx_baseurl',
      props.pieriandxBaseUrlSsmParameterPath
    );

    // Get lambda layer object
    const lambdaLayerObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: 'pieriandx-tools-lambda-layer',
      layerDirectory: path.join(__dirname, '../layers'),
      layerDescription: 'PierianDx Tools Lambda Layer',
    });

    // Collect the pieriandx access token
    const pieriandxTokenCollectionLambdaObj: lambda.IFunction = lambda.Function.fromFunctionName(
      this,
      'pieriandx_auth_token_collection_lambda',
      props.pieriandxAuthTokenCollectionLambdaFunctionName
    );

    // Set Pieriandx secret env for lambdas
    const pieriandxEnvs = {
      PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME: pieriandxTokenCollectionLambdaObj.functionName,
      PIERIANDX_USER_EMAIL: pieriandxUserEmailSsmParameterObj.stringValue,
      PIERIANDX_INSTITUTION: pieriandxInstitutionSsmParameterObj.stringValue,
      PIERIANDX_BASE_URL: pieriandxBaseUrlSsmParameterObj.stringValue,
    };

    const pieriandxSecretEnvs = {
      PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID: pieriandxS3AccessTokenSecretObj.secretName,
    };

    const icav2Envs = {
      ICAV2_BASE_URL: 'https://ica.illumina.com/ica/rest',
      ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
    };

    /*
          Build lambdas
        */
    /* Part 1: Lambdas for generating the PierianDx API objects */
    const generatePieriandxObjectsLambdaObj = new PythonFunction(
      this,
      'generate_pieriandx_objects_lambda_py',
      {
        entry: path.join(__dirname + '/../lambdas/generate_pieriandx_objects_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_pieriandx_objects.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [lambdaLayerObj.lambdaLayerVersionObj],
        timeout: Duration.seconds(60),
        environment: icav2Envs,
      }
    );

    /* Part 2: Lambdas used by the case creation step function */
    /* Generate case lambda object */
    const generateCaseLambdaObj = new PythonFunction(this, 'generate_case_lambda_py', {
      entry: path.join(__dirname + '/../lambdas/generate_case_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_case.py',
      handler: 'handler',
      memorySize: 1024,
      layers: [lambdaLayerObj.lambdaLayerVersionObj],
      timeout: Duration.seconds(30),
      environment: pieriandxEnvs,
    });

    /* Part 3 - Lambdas used by the sequencerrun creation step function */
    /* Generate sequencerrun and samplesheet lambda objects */
    // Simple samplesheet generator object, no env or permissions needed
    const generateSamplesheetLambdaObj = new PythonFunction(
      this,
      'generate_samplesheet_lambda_py',
      {
        entry: path.join(__dirname + '/../lambdas/generate_samplesheet_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_samplesheet.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [lambdaLayerObj.lambdaLayerVersionObj],
        timeout: Duration.seconds(30),
        environment: icav2Envs,
      }
    );

    // Generate sequencerrun object
    const generateSequencerrunLambdaObj = new PythonFunction(
      this,
      'generate_sequencerrun_lambda_py',
      {
        entry: path.join(__dirname + '/../lambdas/generate_sequencerrun_case_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_sequencerrun_case.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [lambdaLayerObj.lambdaLayerVersionObj],
        environment: pieriandxEnvs,
        timeout: Duration.seconds(60),
      }
    );

    // Upload data to S3 lambda object
    const uploadDataToS3LambdaObj = new PythonFunction(
      this,
      'upload_pieriandx_sample_data_to_s3_py',
      {
        entry: path.join(__dirname + '/../lambdas/upload_pieriandx_sample_data_to_s3_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'upload_pieriandx_sample_data_to_s3.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [lambdaLayerObj.lambdaLayerVersionObj],
        timeout: Duration.seconds(300),
        environment: { ...pieriandxEnvs, ...pieriandxSecretEnvs, ...icav2Envs },
      }
    );

    /* Part 4 - Lambdas used by the informatics job creation step function */
    /* Generate informatics job lambda object */
    const generateInformaticsjobLambdaObj = new PythonFunction(
      this,
      'generate_informatics_job_lambda_py',
      {
        entry: path.join(__dirname + '/../lambdas/generate_informaticsjob_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_informaticsjob.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [lambdaLayerObj.lambdaLayerVersionObj],
        timeout: Duration.seconds(30),
        environment: pieriandxEnvs,
      }
    );

    /* Part 5 - Lambdas used by the monitor runs step function */
    const getInformaticsjobAndReportStatusLambdaObj = new PythonFunction(
      this,
      'get_informaticsjob_and_report_status_lambda_obj',
      {
        entry: path.join(__dirname + '/../lambdas/get_informaticsjob_and_report_status_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_informaticsjob_and_report_status.py',
        handler: 'handler',
        memorySize: 1024,
        layers: [lambdaLayerObj.lambdaLayerVersionObj],
        timeout: Duration.seconds(30),
        environment: pieriandxEnvs,
      }
    );

    const generateOutputPayloadDataLambdaObj = new PythonFunction(
      this,
      'generate_output_payload_data_lambda_obj',
      {
        entry: path.join(__dirname + '/../lambdas/generate_output_data_payload_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'generate_output_data_payload.py',
        handler: 'handler',
      }
    );

    /*
        Give the lambda permission to access the pieriandx apis
        */
    [
      generateCaseLambdaObj,
      generateInformaticsjobLambdaObj,
      generateSequencerrunLambdaObj,
      uploadDataToS3LambdaObj,
      getInformaticsjobAndReportStatusLambdaObj,
    ].forEach((lambdaFunction) => {
      // Give the lambda permission to access the pieriandx apis
      // Fixme, no way to give access to only the current version
      pieriandxTokenCollectionLambdaObj.grantInvoke(lambdaFunction.currentVersion);
      NagSuppressions.addResourceSuppressions(
        lambdaFunction,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              'Cannot get latest version of pieriandx collect access token function ($LATEST) will not work',
          },
        ],
        true
      );
    });

    /*
    Give the upload lambda access to the pieriandx s3 bucket
    */
    pieriandxS3AccessTokenSecretObj.grantRead(uploadDataToS3LambdaObj);

    /*
    Give the lambdas permission to access the icav2 apis
    */
    [
      generatePieriandxObjectsLambdaObj,
      generateSamplesheetLambdaObj,
      uploadDataToS3LambdaObj,
    ].forEach((lambdaFunction) => {
      icav2AccessTokenSecretObj.grantRead(lambdaFunction);
    });

    /*
      Generate State Machines
      */

    /* Generate case creation statemachine object */
    const pieriandxLaunchCaseCreationStateMachine =
      new PieriandxLaunchCaseCreationStepFunctionStateMachineConstruct(this, 'case_creation', {
        /* Stack Objects */
        dynamodbTableObj: dynamodbTableObj,
        /* Lambda objs */
        generateCaseLambdaObj: generateCaseLambdaObj,
        /* Step function template */
        launchPieriandxCaseCreationStepfunctionTemplatePath: path.join(
          __dirname,
          '/../step_function_templates/launch_pieriandx_case_creation.asl.json'
        ),
        /* Prefix */
        prefix: props.prefix,
      });

    /* Generate informatics job creation statemachine object */
    const pieriandxInformaticsjobCreationStateMachine =
      new PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstruct(
        this,
        'informaticsjob_creation_sfn',
        {
          /* Stack Objects */
          dynamodbTableObj: dynamodbTableObj,
          /* Lambda paths */
          generateInformaticsjobLambdaObj: generateInformaticsjobLambdaObj,
          /* Step function templates */
          launchPieriandxInformaticsjobCreationStepfunctionTemplate: path.join(
            __dirname,
            '/../step_function_templates/launch_pieriandx_informaticsjob_creation.asl.json'
          ),
          /* Custom */
          prefix: props.prefix,
        }
      );

    /* Generate Sequence Run Creation StateMachine object */
    const pieriandxSequencerrunCreationStateMachine =
      new PieriandxLaunchSequencerrunCreationStepFunctionsStateMachineConstruct(
        this,
        'sequencerrun_creation_sfn',
        {
          /* Stack Objects */
          dynamodbTableObj: dynamodbTableObj,
          /* Lambda paths */
          uploadDataToS3LambdaObj: uploadDataToS3LambdaObj,
          generateSamplesheetLambdaObj: generateSamplesheetLambdaObj,
          generateSequencerrunLambdaObj: generateSequencerrunLambdaObj,
          /* Step function templates */
          launchPieriandxSequencerrunCreationStepfunctionTemplate: path.join(
            __dirname,
            '/../step_function_templates/launch_pieriandx_sequencerrun_creation.asl.json'
          ),
          /* Custom */
          prefix: props.prefix,
        }
      );

    /* Generate parent statemachine object to launch pieriandx analysis */
    const pieriandxLaunchStateMachine = new PieriandxLaunchStepFunctionStateMachineConstruct(
      this,
      id,
      {
        /* Stack Objects */
        dynamodbTableObj: dynamodbTableObj,
        /* Workflow information */
        workflowName: props.workflowName,
        workflowVersion: props.workflowVersion,
        /* Defaults */
        defaultDagVersion: props.defaultDagVersion,
        defaultPanelName: props.defaultPanelName,
        /* Lambdas paths */
        generatePieriandxObjectsLambdaObj: generatePieriandxObjectsLambdaObj,
        /* SSM Parameters */
        dagSsmParameterObj: dagSsmParameterObj,
        panelNameSsmParameterObj: panelNameSsmParameterObj,
        s3SequencerRunRootSsmParameterObj: s3SequencerRunRootSsmParameterObj,
        /* Step function templates */
        launchPieriandxStepfunctionTemplate: path.join(
          __dirname,
          '/../step_function_templates/launch_pieriandx.asl.json'
        ),
        /* Step function objects */
        launchPieriandxCaseCreationStepfunctionObj:
          pieriandxLaunchCaseCreationStateMachine.stateMachineObj,
        launchPieriandxInformaticsjobCreationStepfunctionObj:
          pieriandxInformaticsjobCreationStateMachine.stateMachineObj,
        launchPieriandxSequencerrunCreationStepfunctionObj:
          pieriandxSequencerrunCreationStateMachine.stateMachineObj,
        /* Events */
        detailType: props.eventDetailType,
        eventBusName: props.eventBusName,
        eventSource: props.eventSource,
        payloadVersion: props.payloadVersion,
        triggerLaunchSource: props.triggerLaunchSource,
        /* Custom */
        prefix: props.prefix,
      }
    );

    /* Create the PierianDx Monitor Runs SFN */
    const pieriandxMonitorRunsStateMachine =
      new PieriandxMonitorRunsStepFunctionStateMachineConstruct(this, 'monitor_runs', {
        /* Stack Objects */
        dynamodbTableObj: dynamodbTableObj,
        /* workflow info */
        workflowName: props.workflowName,
        workflowVersion: props.workflowVersion,
        /* Lambda objs */
        getInformaticsjobAndReportStatusLambdaObj: getInformaticsjobAndReportStatusLambdaObj,
        generateOutputPayloadDataLambdaObj: generateOutputPayloadDataLambdaObj,
        /* SSM Parameters */
        pierianDxBaseUrlSsmParameterObj: pieriandxBaseUrlSsmParameterObj,
        /* Step function template */
        launchPieriandxMonitorRunsStepfunctionTemplatePath: path.join(
          __dirname,
          '/../step_function_templates/monitor_runs.asl.json'
        ),
        /* Event info */
        eventBusName: props.eventBusName,
        eventDetailType: props.eventDetailType,
        eventSource: props.eventSource,
        payloadVersion: props.payloadVersion,
        /* Custom */
        prefix: props.prefix,
      });
  }
}
