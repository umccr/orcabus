/*
Standard ICAv2 copy manager

Given a copy manifest, perform the copy job and monitor the ICAv2 eventpipe for copy events 

*/

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { Duration } from 'aws-cdk-lib';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import {
  BuildLambdaProps,
  HandleCopyJobsSfnProps,
  Icav2DataCopyManagerConfig,
  Lambdas,
} from './interfaces';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import { NagSuppressions } from 'cdk-nag';

export type Icav2DataCopyManagerStackProps = Icav2DataCopyManagerConfig & cdk.StackProps;

export class Icav2DataCopyManagerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: Icav2DataCopyManagerStackProps) {
    super(scope, id, props);

    // Get dynamodb table for construct
    const dynamodbTableObj = dynamodb.TableV2.fromTableName(
      this,
      'jobDynamodbTable',
      props.dynamodbTableName
    );

    // Get ICAv2 Access token secret object for construct
    const icav2AccessTokenSecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'Icav2SecretsObject',
      props.icav2AccessTokenSecretId
    );

    // Get the event bus object
    const eventBusObj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Generate the lambdas used by the step functions
    const lambdas = this.build_lambdas({
      icav2AccessTokenSecretObj,
    });

    // Generate the step functions
    const handleCopyJobsSfn = this.generate_handle_copy_jobs({
      /* Naming formation */
      stateMachinePrefix: props.stateMachinePrefix,

      /* Lambdas */
      ...lambdas,

      /* Event Stuff */
      eventBus: eventBusObj,
      icav2CopyServiceEventSource: props.eventSource,
      icav2CopyServiceInternalDetailType: props.eventInternalDetailType,
      icav2CopyServiceExternalDetailType: props.eventExternalDetailType,
    });

    // Generate the Job Collector SFN
    const saveJobAndInternalTaskTokenSfn = this.generate_save_task_token_sfn(
      props.stateMachinePrefix,
      dynamodbTableObj
    );

    // Send the internal task token sfn
    const sendInternalTaskTokenSfn = this.generate_send_internal_task_token_sfn(
      dynamodbTableObj,
      props.stateMachinePrefix,
      handleCopyJobsSfn
    );

    // Create rules
    const generateExternalIcav2CopyJobTriggerRule =
      this.generate_external_icav2_copy_job_trigger_rule(
        eventBusObj,
        props.eventExternalDetailType,
        props.ruleNamePrefix
      );
    const generateInternalIcav2CopyJobTriggerRule =
      this.generate_internal_icav2_copy_job_trigger_rule(
        eventBusObj,
        props.ruleNamePrefix,
        props.eventInternalDetailType,
        props.eventSource
      );

    // Add ica job event pipe rule
    const icaJobEventPipeRule = this.generate_icav2_copy_job_event_pipe_rule(
      eventBusObj,
      props.icaEventPipeName
    );

    // Add the target to the rules
    generateExternalIcav2CopyJobTriggerRule.addTarget(
      new eventsTargets.SfnStateMachine(handleCopyJobsSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
    generateInternalIcav2CopyJobTriggerRule.addTarget(
      new eventsTargets.SfnStateMachine(saveJobAndInternalTaskTokenSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    // Add the target to the task token rule
    icaJobEventPipeRule.addTarget(
      new events_targets.SfnStateMachine(sendInternalTaskTokenSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail.ica-event.payload'),
      })
    );
  }

  private build_lambdas(props: BuildLambdaProps): Lambdas {
    /*
    Generate find single part files lambda function
    */
    const findSinglePartFilesLambdaPythonObject = new PythonUvFunction(
      this,
      'find_single_part_files_py',
      {
        runtime: Runtime.PYTHON_3_12,
        entry: path.join(__dirname, '../lambdas/find_single_part_files_py'),
        architecture: Architecture.ARM_64,
        handler: 'handler',
        index: 'find_single_part_files.py',
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
        },
        memorySize: 1024,
        timeout: Duration.seconds(900),
      }
    );

    /*
    Generate copy job list lambda
    */
    const generateIcav2CopyJobListLambdaPythonObj = new PythonUvFunction(
      this,
      'generate_copy_job_list_py',
      {
        runtime: Runtime.PYTHON_3_12,
        entry: path.join(__dirname, '../lambdas/generate_copy_job_list_py'),
        architecture: Architecture.ARM_64,
        handler: 'handler',
        index: 'generate_copy_job_list.py',
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
        },
        memorySize: 1024,
        timeout: Duration.seconds(900),
      }
    );

    /*
    Lambda ICAv2 Copy Python function
    */
    const launchIcav2CopyLambdaPythonObj = new PythonUvFunction(this, 'launch_icav2_copy_py', {
      runtime: Runtime.PYTHON_3_12,
      entry: path.join(__dirname, '../lambdas/launch_icav2_copy_py'),
      architecture: Architecture.ARM_64,
      handler: 'handler',
      index: 'launch_icav2_copy.py',
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
      },
      memorySize: 1024,
      timeout: Duration.seconds(900),
    });

    /*
    Upload a single part file lambda function
    */
    const uploadSinglePartFileLambdaPythonObject = new PythonUvFunction(
      this,
      'upload_single_part_file_py',
      {
        runtime: Runtime.PYTHON_3_12,
        entry: path.join(__dirname, '../lambdas/upload_single_part_file_py'),
        architecture: Architecture.ARM_64,
        handler: 'handler',
        index: 'upload_single_part_file.py',
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
        },
        memorySize: 1024,
        timeout: Duration.seconds(900),
      }
    );

    // Grant the lambdas access to the secret
    [
      findSinglePartFilesLambdaPythonObject,
      generateIcav2CopyJobListLambdaPythonObj,
      launchIcav2CopyLambdaPythonObj,
      uploadSinglePartFileLambdaPythonObject,
    ].forEach((lambdaFunction) => {
      props.icav2AccessTokenSecretObj.grantRead(lambdaFunction);
    });

    // Return the lambda objects
    return {
      findSinglePartFilesLambdaFunction: findSinglePartFilesLambdaPythonObject,
      generateCopyJobListLambdaFunction: generateIcav2CopyJobListLambdaPythonObj,
      launchIcav2CopyLambdaFunction: launchIcav2CopyLambdaPythonObj,
      uploadSinglePartFileLambdaFunction: uploadSinglePartFileLambdaPythonObject,
    };
  }

  private generate_handle_copy_jobs(props: HandleCopyJobsSfnProps): IStateMachine {
    /*
    Generate the step function to launch the copy job
    */
    // Create the launch copy job sfn
    const handleCopyJobsSfn = new sfn.StateMachine(this, 'handle_copy_jobs', {
      stateMachineName: `${props.stateMachinePrefix}-handle-copy-jobs`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/handle_copy_jobs.asl.json')
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __find_files_with_single_multipart_uploads_lambda_function_arn__:
          props.findSinglePartFilesLambdaFunction.currentVersion.functionArn,
        __generate_copy_jobs_lambda_function_arn__:
          props.generateCopyJobListLambdaFunction.currentVersion.functionArn,
        __launch_copy_job_lambda_function_arn__:
          props.launchIcav2CopyLambdaFunction.currentVersion.functionArn,
        __upload_single_file_lambda_function_arn__:
          props.uploadSinglePartFileLambdaFunction.currentVersion.functionArn,

        /* Events */
        __event_bus_name__: props.eventBus.eventBusName,
        __event_source__: props.icav2CopyServiceEventSource,
        __icav2_copy_job_external_detail_type__: props.icav2CopyServiceExternalDetailType,
        __icav2_copy_job_internal_detail_type__: props.icav2CopyServiceInternalDetailType,
      },
    });

    // Allow sfn to execute the lambda functions
    [
      props.findSinglePartFilesLambdaFunction,
      props.generateCopyJobListLambdaFunction,
      props.launchIcav2CopyLambdaFunction,
      props.uploadSinglePartFileLambdaFunction,
    ].forEach((lambda) => {
      lambda.currentVersion.grantInvoke(handleCopyJobsSfn);
    });

    // Allow sfn to write to event bus
    props.eventBus.grantPutEventsTo(handleCopyJobsSfn);

    // Allow handle copy jobs to send task tokens
    // To any step function
    handleCopyJobsSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [`arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:*`],
        actions: ['states:SendTaskSuccess', 'states:SendTaskFailure'],
      })
    );

    NagSuppressions.addResourceSuppressions(
      handleCopyJobsSfn,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Evaluation state machine needs permissions to send task tokens to any state machine',
        },
      ],
      true
    );

    return handleCopyJobsSfn;
  }

  private generate_save_task_token_sfn(
    stateMachinePrefix: string,
    dynamodbTableObj: dynamodb.ITableV2
  ): IStateMachine {
    // Create the launch copy job sfn
    const saveInternalTaskToken = new sfn.StateMachine(this, 'save_internal_task_token', {
      stateMachineName: `${stateMachinePrefix}-save-internal-task-token`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../step_functions_templates/save_job_and_internal_task_token_in_db.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: dynamodbTableObj.tableName,
      },
    });

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(saveInternalTaskToken);

    return saveInternalTaskToken;
  }

  private generate_send_internal_task_token_sfn(
    dynamodbTableObj: dynamodb.ITableV2,
    stateMachinePrefix: string,
    handleCopyJobsSfn: IStateMachine
  ): IStateMachine {
    /*
    Generate the statemachine that sends the task token for a job id
    */
    // Create the launch copy job sfn
    const sendTaskTokenSfnObj = new sfn.StateMachine(this, 'send_internal_task_token', {
      stateMachineName: `${stateMachinePrefix}-send-internal-task-token`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/send_internal_task_token.asl.json')
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: dynamodbTableObj.tableName,
      },
    });

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(sendTaskTokenSfnObj);

    // Allow step function to send task tokens to the handler sfn
    handleCopyJobsSfn.grantTaskResponse(sendTaskTokenSfnObj);

    // Return the state machine
    return sendTaskTokenSfnObj;
  }

  private generate_internal_icav2_copy_job_trigger_rule(
    eventBusObj: events.IEventBus,
    ruleNamePrefix: string,
    icav2CopyInternalDetailType: string,
    icav2CopyServiceEventSource: string
  ): events.Rule {
    /*
    Internal sync copy jobs
    */
    return new events.Rule(this, 'icav2_copy_job_internal_rule_sync', {
      eventBus: eventBusObj,
      ruleName: `${ruleNamePrefix}-internal-rule`,
      eventPattern: {
        detailType: [icav2CopyInternalDetailType],
        source: [icav2CopyServiceEventSource],
        detail: {
          jobId: [{ exists: true }],
          taskToken: [{ exists: true }],
        },
      },
    });
  }

  private generate_external_icav2_copy_job_trigger_rule(
    eventBusObj: events.IEventBus,
    icav2CopyExternalDetailType: string,
    ruleNamePrefix: string
  ): events.Rule {
    /*
    External sync copy jobs
    */
    return new events.Rule(this, 'icav2_copy_job_external_rule_sync', {
      eventBus: eventBusObj,
      ruleName: `${ruleNamePrefix}-external-rule`,
      eventPattern: {
        detailType: [icav2CopyExternalDetailType],
        detail: {
          sourceUriList: [{ exists: true }],
          destinationUri: [{ exists: true }],
          taskToken: [{ exists: true }],
        },
      },
    });
  }

  private generate_icav2_copy_job_event_pipe_rule(
    eventBusObj: events.IEventBus,
    ruleName: string
  ): events.Rule {
    // Create a rule for this state machine
    return new events.Rule(this, 'rule', {
      eventBus: eventBusObj,
      ruleName: `${ruleName}-rule`,
      eventPattern: {
        detail: {
          'ica-event': {
            // ICA_JOB_)01 is a job state change in ICAv2
            eventCode: ['ICA_JOB_001'],
          },
        },
      },
    });
  }
}
