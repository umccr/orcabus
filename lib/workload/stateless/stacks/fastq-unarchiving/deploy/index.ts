import path from 'path';
import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';

// Importing AWS Lambda related modules
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import { FilemanagerToolsPythonLambdaLayer } from '../../../../components/python-filemanager-tools-layer';
import { FastqToolsPythonLambdaLayer } from '../../../../components/python-fastq-tools-layer';

// Importing AWS DynamoDB related modules
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

// Importing AWS IAM related modules
import * as iam from 'aws-cdk-lib/aws-iam';

// Importing AWS API Gateway related modules
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import {
  HttpMethod,
  HttpNoneAuthorizer,
  HttpRoute,
  HttpRouteKey,
} from 'aws-cdk-lib/aws-apigatewayv2';
import { ApiGatewayConstruct } from '../../../../components/api-gateway';

// Importing AWS SSM and Secrets Manager related modules
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

// Importing AWS EventBridge related modules
import * as events from 'aws-cdk-lib/aws-events';

// Importing AWS S3 related modules
import * as s3 from 'aws-cdk-lib/aws-s3';

// Importing AWS Step Functions related modules
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';

// Importing interfaces
import {
  FastqUnarchivingManagerStackConfig,
  LambdaApiFunctionProps,
  runUnarchivingSfnProps,
  sharedLambdaFunctionObjects,
  sharedLambdaProps,
} from './interfaces';
import { FastqUnarchivingToolsPythonLambdaLayer } from '../../../../components/python-fastq-unarchiving-tools-layer';
import { NagSuppressions } from 'cdk-nag';

export type FastqUnarchivingManagerStackProps = FastqUnarchivingManagerStackConfig & cdk.StackProps;

export class FastqUnarchivingManagerStack extends Stack {
  public readonly API_VERSION = 'v1';
  public readonly UNARCHIVING_URI_PREFIX = 'fastq-unarchiving';

  constructor(scope: Construct, id: string, props: StackProps & FastqUnarchivingManagerStackProps) {
    super(scope, id, props);

    /* Set tables */
    const fastqJobDynamodbTable = dynamodb.TableV2.fromTableName(
      this,
      'jobs_dynamodb_table',
      props.fastqUnarchivingJobsDynamodbTableName
    );

    /* Get event bus */
    const eventBus = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Create the FileManager Tool Layer
    const fileManagerLayer = new FilemanagerToolsPythonLambdaLayer(
      this,
      'filemanager-tools-layer',
      {
        layerPrefix: 'fqu',
      }
    );

    // Create the fastq tools layer
    const fastqToolsLayer = new FastqToolsPythonLambdaLayer(this, 'fastq-tools-layer', {
      layerPrefix: 'fqu',
    });

    // Create the fastq unarchiving tools layer
    const fastqUnarchivingToolsLayer = new FastqUnarchivingToolsPythonLambdaLayer(
      this,
      'fastq-unarchiving-tools-layer',
      {
        layerPrefix: 'fqu',
      }
    );

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

    // Create the shared lambdas used in various step functions
    const sharedLambdas = this.build_shared_lambda_functions_in_sfns({
      /* Fastq Tools */
      fastqUnarchivingManagerToolsLayer: fastqUnarchivingToolsLayer.lambdaLayerVersionObj,
      fastqManagerToolsLayer: fastqToolsLayer.lambdaLayerVersionObj,
      fileManagerToolsLayer: fileManagerLayer.lambdaLayerVersionObj,
      /* SSM and Secrets Manager */
      hostnameSsmParameterObj: hostnameSsmParameterObj,
      orcabusTokenSecretObj: orcabusTokenSecretObj,
    });

    // Build the step functions
    const runUnarchivingSfn = this.build_unarchiving_sfn({
      /* S3StepsCopy */
      s3StepsCopy: props.s3StepsCopy,
      s3Byob: props.s3Byob,
      /* Shared lambdas */
      lambdas: sharedLambdas,
    });

    // Api handler function
    const lambdaFunction = this.build_api_lambda_function({
      /* Tables */
      fastqUnarchivingJobDynamodbTable: fastqJobDynamodbTable,
      /* Table indexes */
      fastqUnarchivingJobsDynamodbIndexes: props.fastqUnarchivingJobsDynamodbIndexes,
      /* SSM and Secrets Manager */
      hostnameSsmParameterObj: hostnameSsmParameterObj,
      orcabusTokenSecretObj: orcabusTokenSecretObj,
      /* Events */
      eventBus: eventBus,
      eventSource: props.eventSource,
      eventDetailType: props.eventDetailType,
      /* SFN */
      fastqUnarchivingStateMachine: runUnarchivingSfn,
    });

    const apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', lambdaFunction);

    // Routes for API schemas
    this.add_http_routes(apiGateway, apiIntegration);
  }

  private build_shared_lambda_functions_in_sfns(
    props: sharedLambdaProps
  ): sharedLambdaFunctionObjects {
    // Generates csv and uploads to s3
    const createCsvForS3StepsCopyLambdaFunction = new PythonUvFunction(
      this,
      'createCsvForS3StepsCopyLambdaFunction',
      {
        entry: path.join(__dirname, '../app/lambdas/create_csv_for_s3_steps_copy_lambda_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'create_csv_for_s3_steps_copy_lambda.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqManagerToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(createCsvForS3StepsCopyLambdaFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(createCsvForS3StepsCopyLambdaFunction.currentVersion);

    const findOriginalIngestIdLambdaFunction = new PythonUvFunction(
      this,
      'findOriginalIngestIdLambdaFunction',
      {
        entry: path.join(__dirname, '../app/lambdas/find_original_ingest_id_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'find_original_ingest_id.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqManagerToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(findOriginalIngestIdLambdaFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(findOriginalIngestIdLambdaFunction.currentVersion);

    // Split fastq ids by instrument run id lambda function
    const splitFastqIdsByInstrumentRunIdLambdaFunction = new PythonUvFunction(
      this,
      'splitFastqIdsByInstrumentRunIdLambdaFunction',
      {
        entry: path.join(
          __dirname,
          '../app/lambdas/split_fastq_ids_by_instrument_run_id_lambda_py'
        ),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'split_fastq_ids_by_instrument_run_id_lambda.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqManagerToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(
      splitFastqIdsByInstrumentRunIdLambdaFunction.currentVersion
    );
    props.hostnameSsmParameterObj.grantRead(
      splitFastqIdsByInstrumentRunIdLambdaFunction.currentVersion
    );

    // Update ingest id lambda function
    const updateIngestIdLambdaFunction = new PythonUvFunction(
      this,
      'updateIngestIdLambdaFunction',
      {
        entry: path.join(__dirname, '../app/lambdas/update_ingest_id_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'update_ingest_id.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fileManagerToolsLayer, props.fastqManagerToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(updateIngestIdLambdaFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(updateIngestIdLambdaFunction.currentVersion);

    // Final function, updating the job database (via the job api)
    const updateJobDatabaseLambdaFunction = new PythonUvFunction(
      this,
      'updateJobDatabaseLambdaFunction',
      {
        entry: path.join(__dirname, '../app/lambdas/update_job_database_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'update_job_database.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqUnarchivingManagerToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(updateJobDatabaseLambdaFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(updateJobDatabaseLambdaFunction.currentVersion);

    return {
      createCsvForS3StepsCopyLambdaFunction: createCsvForS3StepsCopyLambdaFunction,
      findOriginalIngestIdLambdaFunction: findOriginalIngestIdLambdaFunction,
      splitFastqIdsByInstrumentRunIdLambdaFunction: splitFastqIdsByInstrumentRunIdLambdaFunction,
      updateIngestIdLambdaFunction: updateIngestIdLambdaFunction,
      updateJobDatabaseLambdaFunction: updateJobDatabaseLambdaFunction,
    };
  }

  private build_unarchiving_sfn(props: runUnarchivingSfnProps): IStateMachine {
    /* Get s3 steps copy bucket and sfn as objects */
    /* Get s3 steps copy */
    const s3StepsCopyBucket = s3.Bucket.fromBucketName(
      this,
      's3StepsCopyBucket',
      props.s3StepsCopy.s3StepsCopyBucketName
    );
    const s3StepsCopySfn = sfn.StateMachine.fromStateMachineArn(
      this,
      's3StepsCopySfn',
      props.s3StepsCopy.s3StepsFunctionArn
    );

    // Get pipeline cache bucket and prefix
    const s3ByobBucket = s3.Bucket.fromBucketName(this, 's3ByobBucket', props.s3Byob.bucketName);

    // Set up the step function
    const runUnarchivingStateMachine = new sfn.StateMachine(this, 'fastq-unarchiving-sfn', {
      stateMachineName: `fastq-unarchiving-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../app/step_functions_templates/run_s3_steps_copy_sfns_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* S3 Steps copy stuff */
        __aws_s3_copy_steps_bucket__: s3StepsCopyBucket.bucketName,
        __aws_s3_copy_steps_key_prefix__: props.s3StepsCopy.s3StepsCopyPrefix,
        __aws_s3_steps_copy_sfn_arn__: s3StepsCopySfn.stateMachineArn,
        /* Pipeline cache bucket stuff */
        __aws_s3_pipeline_cache_bucket__: props.s3Byob.bucketName,
        __aws_s3_pipeline_cache_restore_prefix__: props.s3Byob.prefix,
        /* Lambdas */
        __update_job_database_lambda_function_arn__:
          props.lambdas.updateJobDatabaseLambdaFunction.currentVersion.functionArn,
        __split_fastq_ids_by_instrument_run_id_lambda_function_arn__:
          props.lambdas.splitFastqIdsByInstrumentRunIdLambdaFunction.currentVersion.functionArn,
        __create_csv_for_s3_steps_copy_lambda_function_arn__:
          props.lambdas.createCsvForS3StepsCopyLambdaFunction.currentVersion.functionArn,
        __get_original_ingest_id_lambda_function_arn__:
          props.lambdas.findOriginalIngestIdLambdaFunction.currentVersion.functionArn,
        __update_ingest_id_lambda_function_arn__:
          props.lambdas.updateIngestIdLambdaFunction.currentVersion.functionArn,
      },
    });

    // Give the state machine permissions to invoke the lambdas
    Object.values(props.lambdas).forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(runUnarchivingStateMachine);
    });

    // Give the createCsvForS3StepsCopyLambdaFunction permission to read/write to the s3 steps copy bucket
    s3StepsCopyBucket.grantReadWrite(
      props.lambdas.createCsvForS3StepsCopyLambdaFunction.currentVersion,
      '*'
    );

    // Give the state machine permissions to invoke the s3 steps copy sfn
    s3StepsCopySfn.grantStartExecution(runUnarchivingStateMachine);

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    runUnarchivingStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // The statemachine also calls itself with a distributed map.
    // We need to add the permissions to the state machine role
    // Unarchiver requires permissions to execute itself
    // Because this steps execution uses a distributed map in its step function, we
    // have to wire up some extra permissions
    // Grant the state machine's role to execute itself
    // However we cannot just grant permission to the role as this will result in a circular dependency
    // between the state machine and the role
    // Instead we use the workaround here - https://github.com/aws/aws-cdk/issues/28820#issuecomment-1936010520
    // packagingStateMachine.grantStartExecution(packagingStateMachine);
    const distributedMapPolicy = new iam.Policy(this, 'sfn-distributed-map-policy', {
      document: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            resources: [runUnarchivingStateMachine.stateMachineArn],
            actions: ['states:StartExecution', 'states:DescribeExecution', 'states:StopExecution'],
          }),
        ],
      }),
    });
    // Add the policy to the state machine role
    runUnarchivingStateMachine.role.attachInlinePolicy(distributedMapPolicy);

    // The distributed map also runs by finding files in the bucket, so we need read permissions on the bucket
    // Note: We actually list objects and then run the distributed map, but we need permissions regardless
    s3ByobBucket.grantRead(runUnarchivingStateMachine, `${props.s3Byob.prefix}*`);

    // Nag suppressions
    NagSuppressions.addResourceSuppressions(
      props.lambdas.createCsvForS3StepsCopyLambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Lambda function creates and uploads a CSV to the bucket, so obviously we need a wildcard',
        },
      ],
      true
    );

    NagSuppressions.addResourceSuppressions(
      runUnarchivingStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Step functions works by finding files in the bucket, so we need read permissions on the bucket and wildcard',
        },
      ],
      true
    );

    return runUnarchivingStateMachine;
  }

  private build_api_lambda_function(props: LambdaApiFunctionProps) {
    const lambdaApiFunction = new PythonUvFunction(this, 'FastqUnarchivingManagerApi', {
      entry: path.join(__dirname, '../app/interface'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'handler.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
      environment: {
        /* DynamoDB env vars */
        DYNAMODB_HOST: `https://dynamodb.${this.region}.amazonaws.com`,
        DYNAMODB_UNARCHIVING_JOB_TABLE_NAME: props.fastqUnarchivingJobDynamodbTable.tableName,
        /* SSM and Secrets Manager env vars */
        HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
        ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        UNARCHIVER_BASE_URL: `https://${this.UNARCHIVING_URI_PREFIX}.${props.hostnameSsmParameterObj.stringValue}`,
        /* Event bridge env vars */
        EVENT_BUS_NAME: props.eventBus.eventBusName,
        EVENT_SOURCE: props.eventSource,
        /* Event detail types */
        EVENT_DETAIL_TYPE_CREATE_JOB: props.eventDetailType.createJob,
        EVENT_DETAIL_TYPE_UPDATE_JOB: props.eventDetailType.updateJob,
        /* SFN env vars */
        UNARCHIVING_JOB_STATE_MACHINE_ARN: props.fastqUnarchivingStateMachine.stateMachineArn,
      },
    });

    // Give lambda function permissions to put events on the event bus
    props.eventBus.grantPutEventsTo(lambdaApiFunction.currentVersion);

    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(lambdaApiFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(lambdaApiFunction.currentVersion);

    // Give lambda execution permissions to the unarchiving sfn
    // Grant Execution permissions to the state machine gives the lambda ability to both
    // start and stop the state machine
    props.fastqUnarchivingStateMachine.grantStartExecution(lambdaApiFunction.currentVersion);

    // Allow read/write access to the dynamodb table
    props.fastqUnarchivingJobDynamodbTable.grantReadWriteData(lambdaApiFunction.currentVersion);

    // Grant query permissions on indexes
    const unarchiving_job_index_arn_list: string[] = props.fastqUnarchivingJobsDynamodbIndexes.map(
      (index_name) => {
        return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.fastqUnarchivingJobDynamodbTable.tableName}/index/${index_name}-index`;
      }
    );
    lambdaApiFunction.currentVersion.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query'],
        resources: unarchiving_job_index_arn_list,
      })
    );

    return lambdaApiFunction;
  }

  // Add the http routes to the API Gateway
  private add_http_routes(apiGateway: ApiGatewayConstruct, apiIntegration: HttpLambdaIntegration) {
    // Routes for API schemas
    new HttpRoute(this, 'GetSchemaHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: new HttpNoneAuthorizer(), // No auth needed for schema
      routeKey: HttpRouteKey.with(`/schema/{PROXY+}`, HttpMethod.GET),
    });
    new HttpRoute(this, 'GetHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.GET),
    });
    new HttpRoute(this, 'PostHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.POST),
    });
    new HttpRoute(this, 'PatchHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.PATCH),
    });
    new HttpRoute(this, 'DeleteHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.DELETE),
    });
  }
}
