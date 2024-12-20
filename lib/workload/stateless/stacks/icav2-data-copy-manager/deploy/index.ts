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
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';

export interface Icav2DataCopyManagerConfig {
  /*
  Tables
  */
  dynamodbTableName: string;

  /*
  Event handling
  */
  eventBusName: string;
  icaEventPipeName: string;

  /*
  Names for statemachines
  */
  stateMachinePrefix: string;

  /*
  Secrets
  */
  icav2TokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
}

export type Icav2DataCopyManagerStackProps = Icav2DataCopyManagerConfig & cdk.StackProps;

export class Icav2DataCopyManagerStack extends cdk.Stack {
  private globals = {
    jobTablePartitionName: 'JobIdToTaskTokenMap',
  };

  private generateLaunchCopyStateMachine(
    dynamodbTableObj: dynamodb.ITableV2,
    icav2AccessTokenSecretObj: secretsManager.ISecret,
    stateMachinePrefix: string
  ): IStateMachine {
    /*
    Generate the step function to launch the copy job
    */

    /*
    Generate input lambdas
    */
    const launchIcav2CopyLambdaPythonObj = new PythonFunction(this, 'launch_icav2_copy_py', {
      runtime: Runtime.PYTHON_3_12,
      entry: path.join(__dirname, '../lambdas/launch_icav2_copy_py'),
      architecture: Architecture.ARM_64,
      handler: 'handler',
      index: 'launch_icav2_copy.py',
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2AccessTokenSecretObj.secretName,
      },
      memorySize: 1024,
      timeout: Duration.seconds(900),
    });

    // Give the lambda function access to the secret
    icav2AccessTokenSecretObj.grantRead(launchIcav2CopyLambdaPythonObj.currentVersion);

    // Create the launch copy job sfn
    const launchCopyJobSfn = new sfn.StateMachine(this, 'launch_copy_job', {
      stateMachineName: `${stateMachinePrefix}-launch-copy-job`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/launch_copy_job.asl.json')
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: dynamodbTableObj.tableName,
        __job_id_partition_name__: this.globals.jobTablePartitionName,
        /* Lambdas */
        __launch_copy_job_lambda_function_arn__:
          launchIcav2CopyLambdaPythonObj.currentVersion.functionArn,
      },
    });

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(launchCopyJobSfn);

    // Configure step function invoke access to the lambda function
    launchIcav2CopyLambdaPythonObj.currentVersion.grantInvoke(launchCopyJobSfn);

    return launchCopyJobSfn;
  }

  private generateSendTaskTokenForJobIdMapStateMachine(
    dynamodbTableObj: dynamodb.ITableV2,
    stateMachinePrefix: string
  ): IStateMachine {
    /*
    Generate the statemachine that sends the task token for a job id
    */
    // Create the launch copy job sfn
    const sendTaskTokenSfnObj = new sfn.StateMachine(this, 'launch_copy_job', {
      stateMachineName: `${stateMachinePrefix}-send-task-token`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/send_task_token.asl.json')
      ),
      definitionSubstitutions: {
        /* Table */
        __table_name__: dynamodbTableObj.tableName,
        __job_id_partition_name__: this.globals.jobTablePartitionName,
      },
    });

    // Configure step function write access to the dynamodb table
    dynamodbTableObj.grantReadWriteData(sendTaskTokenSfnObj);

    // Return the state machine
    return sendTaskTokenSfnObj;
  }

  private generateIcav2CopyJobTriggerRules(
    eventBusObj: events.IEventBus,
    ruleName: string
  ): events.Rule[] {
    /*
    Can't use $or over detailType and detail so use two rules instead
    */
    return [
      // One of
      // detailType == 'ICAv2DataCopySync'
      // And detail contains $.payload.sourceUriList, $.payload.destinationUriList and $.taskToken
      new events.Rule(this, 'icav2_copy_job_trigger_rule_sync', {
        eventBus: eventBusObj,
        ruleName: `${ruleName}-sync-rule`,
        eventPattern: {
          detailType: ['ICAv2DataCopySync'],
          detail: {
            payload: {
              sourceUriList: { exists: true },
              destinationUriList: { exists: true },
            },
            taskToken: { exists: true },
          },
        },
      }),
      // detailType == 'ICAv2DataCopy'
      // And detail contains $.payload.sourceUriList, $.payload.destinationUriList
      new events.Rule(this, 'icav2_copy_job_trigger_rule', {
        eventBus: eventBusObj,
        ruleName: `${ruleName}-rule`,
        eventPattern: {
          detailType: ['ICAv2DataCopy'],
          detail: {
            payload: {
              sourceUriList: { exists: true },
              destinationUriList: { exists: true },
            },
          },
        },
      }),
    ];
  }

  private generateICAv2CopyJobEventPipeRules(
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
      props.icav2TokenSecretId
    );

    // Get the event bus object
    const eventBusObj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Generate the launch sfn
    const launchCopyJobSfn = this.generateLaunchCopyStateMachine(
      dynamodbTableObj,
      icav2AccessTokenSecretObj,
      props.stateMachinePrefix
    );

    // Generate the Job Collector SFN
    const taskTokenSfn = this.generateSendTaskTokenForJobIdMapStateMachine(
      dynamodbTableObj,
      props.stateMachinePrefix
    );

    // Create rules
    const triggerJobRules = this.generateIcav2CopyJobTriggerRules(eventBusObj, 'icav2-copy-job');

    // Add ica job event pipe rule
    const icaJobEventPipeRule = this.generateICAv2CopyJobEventPipeRules(
      eventBusObj,
      props.icaEventPipeName
    );

    // Add the target to the rules
    triggerJobRules.forEach((rule) => {
      rule.addTarget(
        new eventsTargets.SfnStateMachine(launchCopyJobSfn, {
          input: events.RuleTargetInput.fromEventPath('$.detail'),
        })
      );
    });

    // Add the target to the task token rule
    icaJobEventPipeRule.addTarget(
      new events_targets.SfnStateMachine(taskTokenSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail.ica-event'),
      })
    );
  }
}
