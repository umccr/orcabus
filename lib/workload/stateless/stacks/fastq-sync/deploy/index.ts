/*

Generate the four step functions
And add target (slightly modified) events to each https://stackoverflow.com/a/59528479/6946787

Import the following layers
* fastq manager tools
* fastq unarchiving tools

Both these layers are prerequisites for the fastq_sync_tools layer.
For any lambda that uses the fastq sync tools layer, the fastq manager tools and fastq unarchiving tools layers are also required.


Generate the following lambdas

* check fastq set id against requirements
  * Requires fastq tools, fastq sync tools, and so fastq unarchiving tools as well

* check fastq id against requirements
  * Requires fastq tools, fastq sync tools, and so fastq unarchiving tools as well

* get fastq list row ids from fastq set id
  * Requires fastq tools

* get fastq set ids from fastq list row id
  * Requires fastq tools

* Launch requirement job
  * Requires fastq tools, fastq sync tools, and so fastq unarchiving tools as well


Generate the following step functions

* Fastq id updated
  * Converts to list of fastq set ids and launches the fastq set id updated step function

* Fastq set updated
  * Checks fastq set id against any task tokens and checks if requirements for each task token has been satisfied

* Initialise task token for fastq set id sync
  * Initialises task token row in database and appends the task token to the fastq set id in the database
  * Does an immediate check against requirements to see if the fastq set id requirements is already satisfied

* Launch fastq list row requirements
  * Run QC, File Compression stats, ntsm / fingerprint or unarchiving on the fastq list row id if the requirements are not satisfied


Listen to the following events:

* FastqSync -> Synced Event with a taskToken
* FastqSetUpdated -> Triggers the FastqSetUpdated step function
* FastqListRowUpdated -> Triggers the fastq id step function
* FastqUnarchivingComplete -> Triggers the fastq id step function

*/

import path from 'path';
import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';

// Importing AWS Lambda related modules
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import { FastqToolsPythonLambdaLayer } from '../../../../components/python-fastq-tools-layer';
import { FastqSyncToolsPythonLambdaLayer } from '../layers';
import { FastqUnarchivingToolsPythonLambdaLayer } from '../../../../components/python-fastq-unarchiving-tools-layer';

// Importing AWS DynamoDB related modules
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

// Importing AWS IAM related modules
import * as iam from 'aws-cdk-lib/aws-iam';

// Importing AWS SSM and Secrets Manager related modules
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

// Importing AWS EventBridge related modules
import * as events from 'aws-cdk-lib/aws-events';

// Importing AWS Step Functions related modules
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';

// Importing interfaces
import {
  FastqListRowIdUpdatedEventBridgeRuleProps,
  FastqListRowIdUpdatedSfnProps,
  FastqSetIdUpdatedEventBridgeRuleProps,
  FastqSetIdUpdatedSfnProps,
  FastqSyncEventBridgeRuleProps,
  FastqSyncManagerStackConfig,
  FastqUnarchivingCompleteEventBridgeRuleProps,
  InitialiseTaskTokenForFastqSyncSfnProps,
  LambdaBuildInputs,
  Lambdas,
  LaunchFastqListRowRequirementsSfnProps,
} from './interfaces';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { EventField, RuleTargetInput } from 'aws-cdk-lib/aws-events';
import { NagSuppressions } from 'cdk-nag';

export type FastqSyncManagerStackProps = FastqSyncManagerStackConfig & cdk.StackProps;

export class FastqSyncManagerStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & FastqSyncManagerStackProps) {
    super(scope, id, props);

    /* Set tables */
    const fastqSyncDynamodbTable = dynamodb.TableV2.fromTableName(
      this,
      'fastq_sync_dynamodb_table',
      props.fastqSyncDynamodbTableName
    );

    /* Get event bus */
    const eventBus = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Create the External Tool Layers
    const fastqToolsLayer = new FastqToolsPythonLambdaLayer(this, 'fastq-tools-layer', {
      layerPrefix: 'fastqsync',
    });
    const fastqUnarchivingToolsLayer = new FastqUnarchivingToolsPythonLambdaLayer(
      this,
      'fastq-unarchiving-tools-layer',
      {
        layerPrefix: 'fastqsync',
      }
    );

    // Create the internal-use-only fastq sync tool layer
    const fastqSyncToolsLayer = new FastqSyncToolsPythonLambdaLayer(
      this,
      'fastq-sync-tools-layer',
      {
        layerPrefix: 'fastqsync',
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
    const sharedLambdas = this.build_lambda_functions_in_sfns({
      /* Layers Tools */
      fastqToolsLayer: fastqToolsLayer.lambdaLayerVersionObj,
      fastqUnarchivingToolsLayer: fastqUnarchivingToolsLayer.lambdaLayerVersionObj,
      fastqSyncToolsLayer: fastqSyncToolsLayer.lambdaLayerVersionObj,
      /* SSM and Secrets Manager */
      hostnameSsmParameterObj: hostnameSsmParameterObj,
      orcabusTokenSecretObj: orcabusTokenSecretObj,
      /* S3 Stuff */
      pipelineCacheBucketName: props.pipelineCacheBucketName,
      pipelineCachePrefix: props.pipelineCachePrefix,
    });

    // Create the step functions
    const launchFastqListRowRequirementsSfn = this.build_launch_fastq_list_row_requirements_sfn({
      // Lambdas
      getFastqListRowAndRequirementsLambdaFunction:
        sharedLambdas.getFastqListRowAndRequirementsLambdaFunction,
      launchRequirementJobLambdaFunctionArn: sharedLambdas.launchRequirementJobLambdaFunction,
    });

    // Task token intiialiser step function
    // Triggered by a service generating a Fastq Sync event
    const initialiseTaskTokenSfn = this.build_initialise_task_token_for_fastq_sync_sfn({
      // Table
      fastqSyncDynamoDbTable: fastqSyncDynamodbTable,
      // Lambdas
      checkFastqSetIdAgainstRequirementsLambdaFunction:
        sharedLambdas.checkFastqSetIdAgainstRequirementsLambdaFunction,
      getFastqListRowFromFastqSetIdLambdaFunction:
        sharedLambdas.getFastqListRowIdsFromFastqSetIdLambdaFunction,
      // Child step functions
      launchRequirementsSfn: launchFastqListRowRequirementsSfn,
    });

    const fastqSetIdUpdatedSfn = this.build_fastq_set_id_updated_sfn({
      // Table
      fastqSyncDynamoDbTable: fastqSyncDynamodbTable,
      // Lambdas
      checkFastqSetIdAgainstRequirementsLambdaFunction:
        sharedLambdas.checkFastqSetIdAgainstRequirementsLambdaFunction,
      getFastqListRowFromFastqSetIdLambdaFunction:
        sharedLambdas.getFastqListRowIdsFromFastqSetIdLambdaFunction,
      // Child step functions
      launchRequirementsSfn: launchFastqListRowRequirementsSfn,
    });
    const fastqListRowIdUpdatedSfn = this.build_fastq_list_row_id_updated_sfn({
      // Lambdas
      getFastqSetIdsFromFastqListRowIdsLambdaFunction:
        sharedLambdas.getFastqSetIdsFromFastqListRowIdsLambdaFunction,
      // Child step functions
      fastqSetIdUpdatedSfn: fastqSetIdUpdatedSfn,
    });

    // Build up event rules
    this.build_task_token_initialiser_event_rule({
      eventBus: eventBus,
      eventTriggers: props.eventTriggers.fastqSync,
      taskTokenInitialiserSfn: initialiseTaskTokenSfn,
    });

    this.build_fastq_list_row_id_updated_event_rule({
      eventBus: eventBus,
      eventTriggers: props.eventTriggers.fastqListRowUpdated,
      fastqListRowIdUpdatedSfn: fastqListRowIdUpdatedSfn,
    });
    // this.build_fastq_set_id_updated_event_rule({
    //   eventBus: eventBus,
    //   eventTriggers: props.eventTriggers.fastqSetUpdated,
    //   fastqSetIdUpdatedSfn: fastqSetIdUpdatedSfn,
    // });
    this.build_fastq_unarchiving_complete_event_rule({
      eventBus: eventBus,
      eventTriggers: props.eventTriggers.fastqUnarchiving,
      fastqListRowIdUpdatedSfn: fastqListRowIdUpdatedSfn,
    });
  }

  private build_lambda_functions_in_sfns(props: LambdaBuildInputs): Lambdas {
    const checkFastqSetIdAgainstRequirementsLambdaFunction = new PythonUvFunction(
      this,
      'checkFastqSetIdAgainstRequirementsLambdaFunction',
      {
        entry: path.join(__dirname, '../lambdas/check_fastq_set_id_against_requirements_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'check_fastq_set_id_against_requirements.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
          BYOB_BUCKET_PREFIX: `s3://${props.pipelineCacheBucketName}/${props.pipelineCachePrefix}`,
        },
        layers: [
          props.fastqToolsLayer,
          props.fastqSyncToolsLayer,
          props.fastqUnarchivingToolsLayer,
        ],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(
      checkFastqSetIdAgainstRequirementsLambdaFunction.currentVersion
    );
    props.hostnameSsmParameterObj.grantRead(
      checkFastqSetIdAgainstRequirementsLambdaFunction.currentVersion
    );

    const getFastqListRowAndRequirementsLambdaFunction = new PythonUvFunction(
      this,
      'getFastqListRowAndRequirementsLambdaFunction',
      {
        entry: path.join(__dirname, '../lambdas/get_fastq_list_row_and_requirements_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_fastq_list_row_and_requirements.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
          BYOB_BUCKET_PREFIX: `s3://${props.pipelineCacheBucketName}/${props.pipelineCachePrefix}`,
        },
        layers: [
          props.fastqToolsLayer,
          props.fastqSyncToolsLayer,
          props.fastqUnarchivingToolsLayer,
        ],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(
      getFastqListRowAndRequirementsLambdaFunction.currentVersion
    );
    props.hostnameSsmParameterObj.grantRead(
      getFastqListRowAndRequirementsLambdaFunction.currentVersion
    );

    const getFastqListRowIdsFromFastqSetIdLambdaFunction = new PythonUvFunction(
      this,
      'getFastqListRowIdsFromFastqSetIdLambdaFunction',
      {
        entry: path.join(__dirname, '../lambdas/get_fastq_list_row_ids_from_fastq_set_id_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_fastq_list_row_ids_from_fastq_set_id.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(
      getFastqListRowIdsFromFastqSetIdLambdaFunction.currentVersion
    );
    props.hostnameSsmParameterObj.grantRead(
      getFastqListRowIdsFromFastqSetIdLambdaFunction.currentVersion
    );

    const getFastqSetIdsFromFastqListRowIdsLambdaFunction = new PythonUvFunction(
      this,
      'getFastqSetIdsFromFastqListRowIdsLambdaFunction',
      {
        entry: path.join(__dirname, '../lambdas/get_fastq_set_ids_from_fastq_list_row_ids_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_fastq_set_ids_from_fastq_list_row_ids.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(
      getFastqSetIdsFromFastqListRowIdsLambdaFunction.currentVersion
    );
    props.hostnameSsmParameterObj.grantRead(
      getFastqSetIdsFromFastqListRowIdsLambdaFunction.currentVersion
    );

    const launchRequirementJobLambdaFunction = new PythonUvFunction(
      this,
      'launchRequirementJobLambdaFunction',
      {
        entry: path.join(__dirname, '../lambdas/launch_requirement_job_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'launch_requirement_job.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
          BYOB_BUCKET_PREFIX: `s3://${props.pipelineCacheBucketName}/${props.pipelineCachePrefix}`,
        },
        layers: [
          props.fastqToolsLayer,
          props.fastqSyncToolsLayer,
          props.fastqUnarchivingToolsLayer,
        ],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(launchRequirementJobLambdaFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(launchRequirementJobLambdaFunction.currentVersion);

    return {
      checkFastqSetIdAgainstRequirementsLambdaFunction:
        checkFastqSetIdAgainstRequirementsLambdaFunction,
      getFastqListRowAndRequirementsLambdaFunction: getFastqListRowAndRequirementsLambdaFunction,
      getFastqListRowIdsFromFastqSetIdLambdaFunction:
        getFastqListRowIdsFromFastqSetIdLambdaFunction,
      getFastqSetIdsFromFastqListRowIdsLambdaFunction:
        getFastqSetIdsFromFastqListRowIdsLambdaFunction,
      launchRequirementJobLambdaFunction: launchRequirementJobLambdaFunction,
    };
  }

  private build_launch_fastq_list_row_requirements_sfn(
    props: LaunchFastqListRowRequirementsSfnProps
  ): IStateMachine {
    // Set up the step function
    const fqlrRequirementsLauncherStateMachine = new sfn.StateMachine(this, 'fqlrRequirementsSfn', {
      stateMachineName: `fastq-sync-launch-fqlr-requirements-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../step_functions_templates/launch_fastq_list_row_requirements.asl.json'
        )
      ),
      definitionSubstitutions: {
        __get_fastq_list_row_and_requirements_lambda_function_arn__:
          props.getFastqListRowAndRequirementsLambdaFunction.currentVersion.functionArn,
        __launch_requirement_job_lambda_function_arn__:
          props.launchRequirementJobLambdaFunctionArn.currentVersion.functionArn,
      },
    });

    // Give the state machine permissions to invoke the lambdas
    [
      props.getFastqListRowAndRequirementsLambdaFunction,
      props.launchRequirementJobLambdaFunctionArn,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(fqlrRequirementsLauncherStateMachine);
    });

    return fqlrRequirementsLauncherStateMachine;
  }

  private build_initialise_task_token_for_fastq_sync_sfn(
    props: InitialiseTaskTokenForFastqSyncSfnProps
  ): IStateMachine {
    // Set up the step function
    const initialiseTaskTokenForFastqSyncStateMachine = new sfn.StateMachine(
      this,
      'initialiseTaskTokenForFastqSyncSfn',
      {
        stateMachineName: `fastq-sync-initialise-task-token-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            '../step_functions_templates/initialise_task_token_for_fastq_set_id_sync.asl.json'
          )
        ),
        definitionSubstitutions: {
          // Tables
          __dynamodb_table_name__: props.fastqSyncDynamoDbTable.tableName,
          // Lambdas
          __check_fastq_set_id_against_requirements_lambda_function_arn__:
            props.checkFastqSetIdAgainstRequirementsLambdaFunction.currentVersion.functionArn,
          __get_fastq_list_row_from_fastq_set_id_lambda_function_arn__:
            props.getFastqListRowFromFastqSetIdLambdaFunction.currentVersion.functionArn,
          // Child Step functions
          __launch_requirements_sfn_arn__: props.launchRequirementsSfn.stateMachineArn,
        },
      }
    );

    // Give the state machine permissions to read and write to the dynamodb table
    props.fastqSyncDynamoDbTable.grantReadWriteData(initialiseTaskTokenForFastqSyncStateMachine);

    // Give the state machine permissions to invoke the lambdas
    [
      props.checkFastqSetIdAgainstRequirementsLambdaFunction,
      props.getFastqListRowFromFastqSetIdLambdaFunction,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(initialiseTaskTokenForFastqSyncStateMachine);
    });

    // Give the state machine permissions to start the launch requirements step function
    props.launchRequirementsSfn.grantStartExecution(initialiseTaskTokenForFastqSyncStateMachine);

    // Because we run a nested state machine, we need to add the permissions to the parent state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    initialiseTaskTokenForFastqSyncStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Allow initialiser to perform SendTaskSuccess and SendTaskFailure
    // To any step function
    initialiseTaskTokenForFastqSyncStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [`arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:*`],
        actions: ['states:SendTaskSuccess', 'states:SendTaskFailure'],
      })
    );

    NagSuppressions.addResourceSuppressions(
      initialiseTaskTokenForFastqSyncStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Send task status permissions are required for the step function to work, this obviously needs a wildcard',
        },
      ],
      true
    );

    return initialiseTaskTokenForFastqSyncStateMachine;
  }

  private build_fastq_set_id_updated_sfn(props: FastqSetIdUpdatedSfnProps): IStateMachine {
    // Set up the step function
    const fastqSetIdUpdatedStateMachine = new sfn.StateMachine(this, 'fastqSetIdUpdatedSfn', {
      stateMachineName: `fastq-sync-fastq-set-id-updated-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/fastq_set_updated.asl.json')
      ),
      definitionSubstitutions: {
        // Tables
        __dynamodb_table_name__: props.fastqSyncDynamoDbTable.tableName,
        // Lambdas
        __check_fastq_set_id_against_requirements_lambda_function_arn__:
          props.checkFastqSetIdAgainstRequirementsLambdaFunction.currentVersion.functionArn,
        __get_fastq_list_row_from_fastq_set_id_lambda_function_arn__:
          props.getFastqListRowFromFastqSetIdLambdaFunction.currentVersion.functionArn,
        // Child Step functions
        __launch_requirements_sfn_arn__: props.launchRequirementsSfn.stateMachineArn,
      },
    });

    // Give the state machine permissions to read and write to the dynamodb table
    props.fastqSyncDynamoDbTable.grantReadWriteData(fastqSetIdUpdatedStateMachine);

    // Give the state machine permissions to invoke the lambdas
    [
      props.checkFastqSetIdAgainstRequirementsLambdaFunction,
      props.getFastqListRowFromFastqSetIdLambdaFunction,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(fastqSetIdUpdatedStateMachine);
    });

    // Give the state machine permissions to start the launch requirements step function
    props.launchRequirementsSfn.grantStartExecution(fastqSetIdUpdatedStateMachine);

    // Because we run a nested state machine, we need to add the permissions to the parent state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    fastqSetIdUpdatedStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Allow fastq set id updated sfn to send SendTaskSuccess and SendTaskFailure
    // To any step function
    fastqSetIdUpdatedStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [`arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:*`],
        actions: ['states:SendTaskSuccess', 'states:SendTaskFailure'],
      })
    );

    NagSuppressions.addResourceSuppressions(
      fastqSetIdUpdatedStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Send task status permissions are required for the step function to work, this obviously needs a wildcard',
        },
      ],
      true
    );

    return fastqSetIdUpdatedStateMachine;
  }

  private build_fastq_list_row_id_updated_sfn(props: FastqListRowIdUpdatedSfnProps): IStateMachine {
    // Set up the step function
    const fastqListRowIdUpdatedStateMachine = new sfn.StateMachine(
      this,
      'fastqListRowIdUpdatedSfn',
      {
        stateMachineName: `fastq-sync-fastq-list-row-id-updated-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(__dirname, '../step_functions_templates/fastq_id_updated.asl.json')
        ),
        definitionSubstitutions: {
          // Lambdas
          __get_fastq_set_ids_from_fastq_list_row_ids_lambda_function_arn__:
            props.getFastqSetIdsFromFastqListRowIdsLambdaFunction.currentVersion.functionArn,
          // Child Step functions
          __run_fastq_set_id_updated_sfn_arn__: props.fastqSetIdUpdatedSfn.stateMachineArn,
        },
      }
    );

    // Give the state machine permissions to invoke the lambdas
    [props.getFastqSetIdsFromFastqListRowIdsLambdaFunction].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(fastqListRowIdUpdatedStateMachine);
    });

    // Give the state machine permissions to start the launch requirements step function
    props.fastqSetIdUpdatedSfn.grantStartExecution(fastqListRowIdUpdatedStateMachine);

    // Because we run a nested state machine, we need to add the permissions to the parent state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    fastqListRowIdUpdatedStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    return fastqListRowIdUpdatedStateMachine;
  }

  private build_task_token_initialiser_event_rule(props: FastqSyncEventBridgeRuleProps) {
    const eventRule = new events.Rule(this, 'fastqSyncTaskTokenInitialiserRule', {
      ruleName: `fastq-sync-task-token-initialiser-rule`,
      eventBus: props.eventBus,
      eventPattern: {
        detailType: [props.eventTriggers.eventDetailType],
      },
    });

    // Add target to event rule
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(props.taskTokenInitialiserSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }

  private build_fastq_list_row_id_updated_event_rule(
    props: FastqListRowIdUpdatedEventBridgeRuleProps
  ) {
    const eventRule = new events.Rule(this, 'fastqListRowUpdatedFastqSync', {
      ruleName: `fastq-sync-fastq-list-row-updated-event-rule`,
      eventBus: props.eventBus,
      eventPattern: {
        source: [<string>props.eventTriggers.eventSource],
        detailType: [props.eventTriggers.eventDetailType],
        detail: {
          status: [
            { 'equals-ignore-case': 'READ_SET_ADDED' },
            { 'equals-ignore-case': 'FILE_COMPRESSION_UPDATED' },
            { 'equals-ignore-case': 'QC_UPDATED' },
            { 'equals-ignore-case': 'NTSM_UPDATED' },
          ],
        },
      },
    });

    // Add target to event rule
    // Note that we expect fastqListRowIdList as our only input, since the fastqListRowUpdated event detail body
    // Just contains the fastq list row object as is, we need to extract the id from the object and pass it to the target
    // In list format - we use this same step function for the fastq unarchiving which is why we expect our input to be a list
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(props.fastqListRowIdUpdatedSfn, {
        input: RuleTargetInput.fromObject({
          fastqListRowIdList: [EventField.fromPath('$.detail.id')],
        }),
      })
    );
  }

  private build_fastq_set_id_updated_event_rule(props: FastqSetIdUpdatedEventBridgeRuleProps) {
    const eventRule = new events.Rule(this, 'fastqSetUpdatedFastqSync', {
      ruleName: `fastq-sync-fastq-set-updated-event-rule`,
      eventBus: props.eventBus,
      eventPattern: {
        source: [<string>props.eventTriggers.eventSource],
        detailType: [props.eventTriggers.eventDetailType],
      },
    });

    // Add target to event rule
    // Note that we expect fastqListRowId as our only input, since the fastqSetId event detail body
    // Just contains the fastq list row object as is,
    // we need to extract the id from the object and pass it to the target
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(props.fastqSetIdUpdatedSfn, {
        input: RuleTargetInput.fromObject({
          fastqSetId: EventField.fromPath('$.detail.id'),
        }),
      })
    );
  }

  private build_fastq_unarchiving_complete_event_rule(
    props: FastqUnarchivingCompleteEventBridgeRuleProps
  ) {
    const eventRule = new events.Rule(this, 'fastqUnarchivingComplete', {
      ruleName: `fastq-sync-fastq-unarchiving-complete-event-rule`,
      eventBus: props.eventBus,
      eventPattern: {
        source: [<string>props.eventTriggers.eventSource],
        detailType: [props.eventTriggers.eventDetailType],
        detail: {
          status: [{ 'equals-ignore-case': 'SUCCEEDED' }],
        },
      },
    });

    // Add target to event rule
    // Note that we expect fastqListRowIdList as our only input
    // While the fastqUnarchivingComplete event detail body contains the fastq list row objects we need to
    // rename the list to match the input requirements of the step function
    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(props.fastqListRowIdUpdatedSfn, {
        input: RuleTargetInput.fromObject({
          fastqListRowIdList: EventField.fromPath('$.detail.fastqIds'),
        }),
      })
    );
  }
}
